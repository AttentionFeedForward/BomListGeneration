from typing import Dict, List, Tuple
from mep_semantics import Edge

def shortest_paths(edges: List[Edge]) -> Dict[Tuple[str, str], float]:
    nodes: Dict[str, List[Tuple[str, float]]] = {}
    for e in edges:
        nodes.setdefault(e.a, []).append((e.b, e.weight))
        nodes.setdefault(e.b, []).append((e.a, e.weight))
    result: Dict[Tuple[str, str], float] = {}
    for src in nodes.keys():
        dist: Dict[str, float] = {n: float('inf') for n in nodes.keys()}
        dist[src] = 0.0
        visited: Dict[str, bool] = {}
        while True:
            u = None
            best = float('inf')
            for n, d in dist.items():
                if not visited.get(n) and d < best:
                    u, best = n, d
            if u is None:
                break
            visited[u] = True
            for v, w in nodes.get(u, []):
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
        for dst, d in dist.items():
            if d < float('inf') and src != dst:
                result[(src, dst)] = d
    return result
