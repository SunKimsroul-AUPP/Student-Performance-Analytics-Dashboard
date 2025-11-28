from typing import Dict, List, Set


class PrereqGraph:
    """
    Directed graph where edges go: course -> prerequisite.
    Provides cycle detection and depth computation.
    """

    def __init__(self):
        self.adj: Dict[str, List[str]] = {}
        self.nodes: Set[str] = set()

    def add_course(self, course_id: str) -> None:
        self.nodes.add(course_id)
        self.adj.setdefault(course_id, [])

    def add_edge(self, course_id: str, prereq_id: str) -> None:
        self.add_course(course_id)
        self.add_course(prereq_id)
        self.adj[course_id].append(prereq_id)

    def get_prereqs(self, course_id: str) -> List[str]:
        return self.adj.get(course_id, [])

    def has_cycle(self) -> bool:
        visited, stack = set(), set()

        def dfs(u: str) -> bool:
            visited.add(u)
            stack.add(u)
            for v in self.adj.get(u, []):
                if v not in visited and dfs(v):
                    return True
                if v in stack:
                    return True
            stack.remove(u)
            return False

        return any(dfs(node) for node in self.nodes if node not in visited)

    def depth(self, course_id: str) -> int:
        """
        Longest chain of prerequisites (0 if none).
        """
        memo: Dict[str, int] = {}

        def rec(c: str) -> int:
            if c in memo:
                return memo[c]
            pres = self.adj.get(c, [])
            if not pres:
                memo[c] = 0
            else:
                memo[c] = 1 + max(rec(p) for p in pres)
            return memo[c]

        return rec(course_id)