
# backend/graph/build_graph.py

from typing import Callable, Dict, List


def build_graph() -> Dict[str, List[str]]:
    """
    BUILD GRAPH

    Defines the execution graph for the multi-agent pipeline.
    Nodes are agent names, edges define execution order.
    """

    graph = {
        "retriever": ["generator"],
        "generator": ["fact_checker"],
        "fact_checker": ["citation"],
        "citation": ["summariser"],
        "summariser": []
    }

    return graph
