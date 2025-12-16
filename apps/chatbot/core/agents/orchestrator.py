import os
import operator
from logging import Logger
from typing import Any, Dict, TypedDict, Annotated, List

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from core.agents.resume_extract_agent import ResumeExtractAgent
from core.agents.jd_extract_agent import JDExtractAgent
from core.agents.evaluation_agent import EvaluationAgent
from core.factories.llm_factory import LLMFactory
from core.agents.state import State

from dotenv import load_dotenv

load_dotenv()


class Orchestrator:
    def __init__(self):
        self.logger = Logger("orchestrator")
        model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        api_key = os.environ.get("GROQ_API_KEY")
        
        self.llm = LLMFactory.create_llm(
            llm_provider=LLMFactory.Provider.GROQ,
            config=LLMFactory.LLMConfig(model_name=model_name, api_key=api_key),
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

            # Define Node Wrappers
            def resume_node(state: State):
                self.logger.info("Executing Resume Node")
                resume_path = state.get("resume_path")
                if not resume_path:
                    raise ValueError("resume_path is missing in state")
                
                result = resume_extract_agent.extract_resume(resume_path)
                # Map 'resume' from agent result to 'resume_text' in State
                return {"resume_text": result["resume"]}

            def jd_node(state: State):
                self.logger.info("Executing JD Node")
                jd_path = state.get("jd_path")
                if not jd_path:
                    raise ValueError("jd_path is missing in state")
                
                result = jd_extract_agent.extract_jd(jd_path)
                # Map first 'jds' item from agent result to 'jd_text' in State
                jds = result.get("jds", [])
                if not jds:
                     raise ValueError("No JDs found")
                
                # Assuming we take the first JD for evaluation
                return {"jd_text": jds[0]}

            def evaluation_node(state: State):
                self.logger.info("Executing Evaluation Node")
                resume = state.get("resume_text")
                jd = state.get("jd_text")
                
                if not resume or not jd:
                    raise ValueError("Missing resume or JD for evaluation")

                result_content = evaluation_agent.evaluate(resume, jd)
                return {"messages": [result_content]}

            # Graph
            builder = StateGraph(State)
            
            # Nodes
            builder.add_node("resume_extract_agent", resume_node)
            builder.add_node("jd_extract_agent", jd_node)
            builder.add_node("evaluation_agent", evaluation_node)
            
            # Edges
            builder.add_edge(START, "resume_extract_agent")
            builder.add_edge("resume_extract_agent", "jd_extract_agent")
            builder.add_edge("jd_extract_agent", "evaluation_agent")
            builder.add_edge("evaluation_agent", END)

            # Build
            self.graph = builder.compile()
            return self.graph

        except Exception as ex:
            self.logger.error(f"Error while build graph: {ex}")
            raise ex

    def export_graph(self, path: str) -> None:
        try:
            if self.graph is None:
                self.orchestrate()
            
            p = os.path.join(os.getcwd(), path)
            with open(p, "wb") as f:
                f.write(self.graph.get_graph().draw_mermaid_png())
            self.logger.info(f"Graph exported to {p}")
        except Exception as e:
            self.logger.error(f"Error while export diagram {e}")
