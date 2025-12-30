import os
import traceback
import logging
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph, START, END

from core.agents.base_agent import BaseAgent
from core.agents.state import State
from core.agents.resume_extract_agent import ResumeExtractAgent
from core.agents.jd_extract_agent import JDExtractAgent
from core.agents.evaluation_agent import EvaluationAgent
from core.agents.retrieval_agent import RetrievalAgent
from core.factories.llm_factory import LLMFactory
from config.config import config

from dotenv import load_dotenv

load_dotenv()


class Orchestrator:
    """Orchestrator class for manage langgraph"""

    def __init__(self):
        self.logger = logging.getLogger("orchestrator")

        self.llm = LLMFactory.create_llm(
            llm_provider=LLMFactory.Provider.BEDROCK,
            config=LLMFactory.LLMConfig(
                model_name=config.BEDROCK_LLM_MODEL,
                model_region=config.BEDROCK_MODEL_REGION,
            ),
        )
        self.tools = ["docx_loader", "pdf_loader"]
        self.graph = None

    def orchestrate(self) -> CompiledStateGraph:
        try:
            # Init agents
            resume_extract_agent = ResumeExtractAgent(
                "resume_agent", self.llm, self.tools
            )
            jd_extract_agent = JDExtractAgent("jd_agent", self.llm, self.tools)
            evaluation_agent = EvaluationAgent("evaluation_agent", self.llm, self.tools)
            retrieval_agent = RetrievalAgent("retrieval_agent", self.llm, self.tools)

            # Define Node Wrappers
            def resume_node(state: State):
                """Extract resume from file path or use existing text in state."""
                try:
                    self.logger.info("Executing Resume Node")

                    # Check if resume text already exists (from API)
                    if state.get("resume_text"):
                        self.logger.info("Using existing resume text from state")
                        return {"resume_text": state["resume_text"]}

                    # Otherwise extract from file path
                    resume_path = state.get("resume_path")
                    if not resume_path:
                        raise ValueError(
                            "Neither resume_text nor resume_path provided in state"
                        )

                    result = resume_extract_agent.extract_resume(resume_path)
                    return {"resume_text": result["resume"]}
                except Exception as e:
                    self.logger.error(
                        f"Resume node failed: {e}\n{traceback.format_exc()}"
                    )
                    raise

            def jd_node(state: State):
                """Extract job descriptions from file path or use existing text in state."""
                try:
                    self.logger.info("Executing JD Node")

                    # Check if JD text already exists (from API)
                    if state.get("jd_text"):
                        self.logger.info("Using existing JD text from state")
                        return {"jd_text": state["jd_text"]}

                    # Otherwise extract from file path
                    jd_path = state.get("jd_path")
                    if not jd_path:
                        raise ValueError(
                            "Neither jd_text nor jd_path provided in state"
                        )

                    result = jd_extract_agent.extract_jd(jd_path)
                    jds = result.get("jds", [])
                    # JD agent now validates this, but double-check
                    if not jds:
                        raise ValueError("No JDs found")

                    return {"jd_text": jds[0]}
                except Exception as e:
                    self.logger.error(f"JD node failed: {e}\n{traceback.format_exc()}")
                    raise

            def evaluation_node(state: State):
                """Evaluate resume against job description."""
                try:
                    self.logger.info("Executing Evaluation Node")
                    resume = state.get("resume_text")
                    jd = state.get("jd_text")

                    if not resume or not jd:
                        raise ValueError("Missing resume or JD for evaluation")

                    result_content = evaluation_agent.evaluate(resume, jd)
                    return {"messages": [result_content]}
                except Exception as e:
                    self.logger.error(
                        f"Evaluation node failed: {e}\n{traceback.format_exc()}"
                    )
                    raise

            def retrieval_node(state: State):
                """Retrieve similar jobs from vector database with skill-based filtering."""
                try:
                    self.logger.info("Executing Retrieval Node")
                    resume_text = state.get("resume_text")

                    # Extract hard skills from resume for skill-based filtering
                    resume_skills = []
                    if hasattr(resume_text, "hard_skills") and resume_text.hard_skills:
                        resume_skills = resume_text.hard_skills
                        self.logger.info(
                            f"Extracted {len(resume_skills)} hard skills from resume"
                        )

                    # Build focused query from skills and summary for better matching
                    query_parts = []

                    if hasattr(resume_text, "hard_skills") and resume_text.hard_skills:
                        skills_str = ", ".join(resume_text.hard_skills)
                        query_parts.append(f"Skills: {skills_str}")

                    if hasattr(resume_text, "soft_skills") and resume_text.soft_skills:
                        soft_skills_str = ", ".join(resume_text.soft_skills)
                        query_parts.append(f"Soft Skills: {soft_skills_str}")

                    if (
                        hasattr(resume_text, "profile_summary")
                        and resume_text.profile_summary
                    ):
                        query_parts.append(f"Profile: {resume_text.profile_summary}")

                    # Fallback to full text if no structured fields available
                    if query_parts:
                        query_text = "\n".join(query_parts)
                    elif hasattr(resume_text, "model_dump_json"):
                        query_text = resume_text.model_dump_json()
                    else:
                        query_text = str(resume_text)

                    self.logger.info(f"Retrieval query: {query_text[:200]}...")

                    # Call retrieve with skill filtering (min 10% skill match)
                    results = retrieval_agent.retrieve(
                        query=query_text,
                        k=5,
                        resume_skills=resume_skills,
                        min_skill_match=10.0,  # Require at least 10% skill match
                    )

                    # Format results for display
                    formatted_results = retrieval_agent.format_results_for_display(
                        results
                    )

                    return {"retrieved_jobs": formatted_results}
                except Exception as e:
                    self.logger.error(
                        f"Retrieval node failed: {e}\n{traceback.format_exc()}"
                    )
                    raise

            # Graph
            builder = StateGraph(State)

            # Nodes
            builder.add_node("resume_extract_agent", resume_node)
            builder.add_node("jd_extract_agent", jd_node)
            builder.add_node("evaluation_agent", evaluation_node)
            builder.add_node("retrieval_agent", retrieval_node)

            # Edges - Parallel execution for resume and JD extraction (faster!)
            builder.add_edge(START, "resume_extract_agent")
            builder.add_edge(START, "jd_extract_agent")  # Run in parallel with resume
            builder.add_edge("resume_extract_agent", "evaluation_agent")
            builder.add_edge(
                "jd_extract_agent", "evaluation_agent"
            )  # Both feed into evaluation
            builder.add_edge("evaluation_agent", "retrieval_agent")
            builder.add_edge("retrieval_agent", END)

            # Build
            self.graph = builder.compile()
            return self.graph

        except Exception as ex:
            self.logger.error(
                f"Error while building graph: {ex}\n{traceback.format_exc()}"
            )
            raise RuntimeError("Failed to build LangGraph orchestrator") from ex

    def export_graph(self, path: str) -> None:
        try:
            if self.graph is None:
                self.orchestrate()

            p = os.path.join(os.getcwd(), path)
            with open(p, "wb") as f:
                f.write(self.graph.get_graph().draw_mermaid_png())
            self.logger.info(f"Graph exported to {p}")
        except Exception as e:
            self.logger.error(
                f"Error while exporting diagram: {e}\n{traceback.format_exc()}"
            )
            raise
