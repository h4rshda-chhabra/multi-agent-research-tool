from typing import Optional
from langgraph.graph import StateGraph, END

from app.agents.state import ResearchState
from app.agents.planner import planner_node
from app.agents.search import search_node
from app.agents.validator import validator_node
from app.agents.extractor import extractor_node
from app.agents.synthesizer import synthesizer_node


def _should_continue(state: ResearchState) -> str:
    """Route to END if an error occurred; otherwise continue normally."""
    return END if state.get("error") else "continue"


def build_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("search", search_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("planner")

    # After each node: stop on error, otherwise advance
    for src, dst in [
        ("planner", "search"),
        ("search", "validator"),
        ("validator", "extractor"),
        ("extractor", "synthesizer"),
    ]:
        workflow.add_conditional_edges(
            src,
            _should_continue,
            {"continue": dst, END: END},
        )

    workflow.add_edge("synthesizer", END)
    return workflow.compile()


# Module-level compiled graph (single instance)
research_graph = build_graph()
