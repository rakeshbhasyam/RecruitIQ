import uuid
from typing import TypedDict, Optional, Dict, Any, List

from langgraph.graph import StateGraph, END

from app.agents import (
    ResumeIngestionAgent,
    ResumeParserAgent,
    ResumeMatcherAgent,
    InterviewAgent,
    FinalScoringAgent,
)
from app.config.database import db

# Initialize agents
ingestion_agent = ResumeIngestionAgent()
parser_agent = ResumeParserAgent()
matcher_agent = ResumeMatcherAgent()
interview_agent = InterviewAgent()
scoring_agent = FinalScoringAgent()


# 1. Define the state for the graph
class AgentState(TypedDict):
    """Represents the state of our agentic workflow."""
    trace_id: str
    candidate_id: str
    job_id: str
    file_path: str
    resume_text: Optional[str]
    candidate_profile: Optional[Dict[str, Any]]
    job_match_report: Optional[Dict[str, Any]]
    interview_criteria: Optional[Dict[str, Any]]
    final_score: Optional[float]
    final_report: Optional[Dict[str, Any]]


# 2. Define the nodes for the graph
async def resume_analyzer_node(state: AgentState) -> AgentState:
    """
    Node 1: Ingests and parses the resume.
    Corresponds to the "Resume Analyzer Agent".
    """
    print("---Executing Resume Analyzer Node---")
    trace_id = state["trace_id"]
    candidate_id = state["candidate_id"]
    file_path = state["file_path"]

    # Ingest (extract text)
    ingestion_result = await ingestion_agent.process_resume(candidate_id, file_path, trace_id)
    state["resume_text"] = ingestion_result["extracted_text"]

    # Parse (extract structured data)
    parsed_data = await parser_agent.parse_resume(candidate_id, state["resume_text"], trace_id)
    state["candidate_profile"] = parsed_data
    return state


async def job_matcher_node(state: AgentState) -> AgentState:
    """
    Node 2: Compares candidate profile with job description.
    Corresponds to the "Job Matcher Agent".
    """
    print("---Executing Job Matcher Node---")
    trace_id = state["trace_id"]
    candidate_id = state["candidate_id"]
    job_id = state["job_id"]

    match_report = await matcher_agent.match_candidate(candidate_id, job_id, trace_id)
    state["job_match_report"] = match_report
    return state


async def interview_criteria_node(state: AgentState) -> AgentState:
    """
    Node 3: Generates interview criteria and sample questions.
    Corresponds to the "Interview Criteria Agent".
    """
    print("---Executing Interview Criteria Node---")
    trace_id = state["trace_id"]
    candidate_id = state["candidate_id"]
    job_id = state["job_id"]

    # Using generate_questions method, but with a prompt that creates criteria
    interview_criteria = await interview_agent.generate_questions(
        candidate_id, job_id, trace_id, num_questions=3, generate_criteria=True
    )
    state["interview_criteria"] = {"criteria": interview_criteria}
    return state


async def final_scorer_node(state: AgentState) -> AgentState:
    """
    Node 4: Calculates the final score and generates a unified report.
    Corresponds to the "Coordinator Agent's" finalization step.
    """
    print("---Executing Final Scorer Node---")
    trace_id = state["trace_id"]
    candidate_id = state["candidate_id"]
    job_id = state["job_id"]

    # Calculate final score (this will use the matcher_score already in DB)
    final_result = await scoring_agent.calculate_final_score(candidate_id, job_id, trace_id)
    state["final_score"] = final_result.get("final_score")

    # Generate unified report
    candidate = await db.candidates.get_candidate(candidate_id)
    job = await db.jobs.get_job(job_id)

    state["final_report"] = {
        "candidate": candidate.get("parsed_data", {}).get("name", "N/A"),
        "role": job.get("title", "N/A"),
        "overall_match_score": state["final_score"],
        "criteria_table": state.get("job_match_report", {}).get("detailed_analysis"),
        "interview_criteria": state.get("interview_criteria"),
        "recommendation": "Strong candidate for technical interview" if state["final_score"] > 0.7 else "Further review recommended"
    }
    return state


# 3. Define the graph
def build_graph():
    """Builds and compiles the LangGraph for the recruitment workflow."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("resume_analyzer", resume_analyzer_node)
    workflow.add_node("job_matcher", job_matcher_node)
    workflow.add_node("interview_criteria_generator", interview_criteria_node)
    workflow.add_node("final_scorer", final_scorer_node)

    # Define edges
    workflow.set_entry_point("resume_analyzer")
    workflow.add_edge("resume_analyzer", "job_matcher")
    workflow.add_edge("job_matcher", "interview_criteria_generator")
    workflow.add_edge("interview_criteria_generator", "final_scorer")
    workflow.add_edge("final_scorer", END)

    # Compile the graph
    app = workflow.compile()
    return app


# Create a singleton instance of the compiled graph
recruitment_graph = build_graph()