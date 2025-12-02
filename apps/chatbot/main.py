from core.agents.resume_extract_agent import ResumeExtractAgent
from core.agents.jd_extract_agent import JDExtractAgent
from core.agents.orchestrator import Orchestrator


if __name__ == "__main__":
    config = Orchestrator()
    resume = ResumeExtractAgent("hihi", config.llm, config.tools)
    result = resume.extract_resume("resume/Cao_Minh_Tri_Resume.pdf")
    print("-" * 20)
    jd = JDExtractAgent("haha", config.llm, config.tools)
    result_jd = jd.extract_jd("resume/url.docx")
    print(result_jd)
