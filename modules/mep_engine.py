from typing import Dict, Any, List
from mep_semantics import build_rooms, Topology
from mep_rule_engine import load_bs, min_fixture_counts
from mep_point_placer import place_points
from mep_layout import assign_coordinates_and_layout
from mep_graph import build_topology
from mep_routing import shortest_paths
from mep_wiring_calculator import material_breakdown, aggregate_lengths
from mep_validator import rules_check, deviation_check

def generate(floorplan: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    bs = load_bs()
    rooms = build_rooms(floorplan.get('rooms', []))
    counts_by_room: Dict[str, Dict[str, int]] = {}
    for r in rooms:
        counts_by_room[r.name] = min_fixture_counts(bs, project_type, r.room_type)
    
    # 1. Place Points (Logical)
    points = place_points(rooms, project_type, counts_by_room)
    
    # 2. Layout & Coordinates (Physical)
    # This also generates Doors based on adjacency
    doors = assign_coordinates_and_layout(rooms, points)
    
    # 3. Topology & Routing (Graph)
    topo: Topology = build_topology(rooms, points, doors)
    
    # 4. Calculation
    # sp = shortest_paths(topo.edges) # Not strictly needed for topology list, but good for analysis
    materials = []
    materials.extend(material_breakdown(bs, project_type, '其余', topo))
    totals = aggregate_lengths(topo)
    
    # Calculate total electrical pipe length for deviation check
    elec_len = totals.get('strong_electric', {}).get('trunk', 0.0) + totals.get('strong_electric', {}).get('branch', 0.0)
    
    dev = deviation_check(bs, project_type, sum(r.area for r in rooms), elec_len)
    
    # Merge counts for validation
    merged_counts = merge_counts(counts_by_room)
    actual = actual_counts(points)
    rules = rules_check(min_counts=merged_counts, actual_counts=actual)
    
    return {
        'points': [as_point(p) for p in points],
        'topology': [as_edge(e) for e in topo.edges],
        'doors': [{'room_a': d.room_a, 'room_b': d.room_b, 'x': d.coordinate.x, 'y': d.coordinate.y} for d in doors],
        'materials': materials,
        'validation': {
            'rules': rules,
            'deviation': [dev]
        }
    }

def merge_counts(d: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    res: Dict[str, int] = {}
    for _, v in d.items():
        for k, c in v.items():
            res[k] = res.get(k, 0) + int(c)
    return res

def actual_counts(points) -> Dict[str, int]:
    res: Dict[str, int] = {}
    for p in points:
        if p.subtype == 'light':
            res['照明灯具'] = res.get('照明灯具', 0) + 1
        if p.subtype == 'switch':
            res['开关'] = res.get('开关', 0) + 1
        if 'socket' in p.subtype:
            res['插座'] = res.get('插座', 0) + 1
        if p.subtype in ['box', 'db_box', 'elv_box']:
            res['底盒'] = res.get('底盒', 0) + 1
    return res

def as_point(p):
    res = {'id': p.id, 'system': p.system, 'type': p.subtype, 'room': p.room_name, 'anchor': p.anchor}
    if p.coordinate:
        res['coordinate'] = {'x': round(p.coordinate.x, 2), 'y': round(p.coordinate.y, 2), 'z': round(p.coordinate.z, 2)}
    return res

def as_edge(e):
    res = {'from': e.a, 'to': e.b, 'length': round(e.weight, 2), 'kind': e.kind, 'routing': e.routing_type, 'circuit_id': getattr(e, 'circuit_id', '')}
    if e.waypoints:
        res['waypoints'] = [{'x': round(w.x, 2), 'y': round(w.y, 2), 'z': round(w.z, 2)} for w in e.waypoints]
    return res
