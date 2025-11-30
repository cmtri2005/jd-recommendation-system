from core.agents.resume_extract_agent import ResumeExtractAgent
from core.agents.orchestrator import Orchestrator


if __name__ == "__main__":
    config = Orchestrator()
    resume = ResumeExtractAgent("hihi",config.llm, config.tools)
    result = resume.extract_resume("resume/Cao_Minh_Tri_Resume.pdf")
    print(result)