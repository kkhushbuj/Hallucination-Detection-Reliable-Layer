from langgraph.graph import StateGraph, END
from typing import TypedDict
from core.verification import run_verification_check


class TrustScoreState(TypedDict):
    question: str
    verification_result: dict


def verification_node(state: TrustScoreState) -> TrustScoreState:
    state["verification_result"] = run_verification_check(state["question"])
    return state


def build_graph():
    graph = StateGraph(TrustScoreState)
    graph.add_node("verification", verification_node)
    graph.set_entry_point("verification")
    graph.add_edge("verification", END)
    return graph.compile()