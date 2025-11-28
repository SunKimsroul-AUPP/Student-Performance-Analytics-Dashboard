import pandas as pd
from typing import Dict, Any
from ..graph.prereq_graph import PrereqGraph


class GraphService:
    """
    Wraps PrereqGraph into dataset-aware operations.
    """

    def __init__(self, prereqs_df: pd.DataFrame, courses_df: pd.DataFrame = None):
        self.graph = PrereqGraph()
        for _, row in prereqs_df.iterrows():
            self.graph.add_edge(row["course_id"], row["prereq_id"])
        # Optional mapping of course_id -> title
        self.course_titles = {}
        if courses_df is not None:
            for _, r in courses_df.iterrows():
                cid = r.get("course_id")
                title = r.get("title") or r.get("name") or None
                if cid:
                    self.course_titles[str(cid)] = title

    def summary(self) -> Dict[str, Any]:
        cycle = self.graph.has_cycle()
        depths = {c: self.graph.depth(c) for c in self.graph.nodes}
        dependents = {c: 0 for c in self.graph.nodes}
        for course, pres in self.graph.adj.items():
            for p in pres:
                dependents[p] = dependents.get(p, 0) + 1
        gateways = sorted(dependents.items(), key=lambda x: -x[1])[:5]
        # Convert to list of dicts for stable JSON / pydantic parsing
        gateway_list = []
        for c, cnt in gateways:
            item = {"course_id": c, "dependents": cnt}
            title = self.course_titles.get(str(c))
            if title:
                item["title"] = title
            gateway_list.append(item)

        return {
            "cycle_detected": cycle,
            "depths": depths,
            "gateway_candidates": gateway_list,
        }

    def adjacency(self) -> Dict[str, Any]:
        # Return adjacency with optional titles for each prerequisite
        out: Dict[str, Any] = {}
        for course, pres in self.graph.adj.items():
            lst = []
            for p in pres:
                item = {"course_id": p}
                title = self.course_titles.get(str(p))
                if title:
                    item["title"] = title
                lst.append(item)
            out[course] = lst
        return out