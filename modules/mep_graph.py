from typing import List, Dict, Tuple, Optional, Set
import math
import collections
from mep_semantics import Point, Edge, Topology, Room, Coordinate, Door

def get_routing_distance(c1: Coordinate, c2: Coordinate, method='floor') -> float:
    # 1. Vertical segments
    if method == 'ceiling':
        # Up to 2.8m
        v1 = abs(2.8 - c1.z)
        v2 = abs(2.8 - c2.z)
        h = abs(c1.x - c2.x) + abs(c1.y - c2.y)
        return v1 + h + v2
    elif method == 'floor':
        # Down to 0m (or -0.1m for embedded)
        v1 = c1.z
        v2 = c2.z
        h = abs(c1.x - c2.x) + abs(c1.y - c2.y)
        return v1 + h + v2
    else: # direct/wall
        return math.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2 + (c1.z - c2.z)**2)

def bfs_room_path(start_room: str, end_room: str, doors: List[Door]) -> List[Door]:
    if start_room == end_room: return []
    
    # Build adjacency
    adj = collections.defaultdict(list)
    for d in doors:
        adj[d.room_a].append((d.room_b, d))
        adj[d.room_b].append((d.room_a, d))
        
    # BFS
    queue = collections.deque([(start_room, [])])
    visited = {start_room}
    
    while queue:
        curr, path = queue.popleft()
        if curr == end_room:
            return path
            
        for neighbor, door in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = path + [door]
                queue.append((neighbor, new_path))
                
    return [] # No path found (disconnected)

def get_path_distance(p1: Point, p2: Point, doors: List[Door], routing_type='floor') -> Tuple[float, List[Coordinate]]:
    """
    Returns (distance, waypoints)
    Waypoints include [p1, door1, door2, ..., p2] (excluding start/end if you just want intermediates, 
    but for visualization we might want the full path or just the door transits).
    Here we return the *intermediate* key points (Doors) + endpoints effectively handled by caller or visualization.
    Actually, let's return the full sequence of "turning points" if possible, but simplest is just the door centers.
    """
    if p1.room_name == p2.room_name:
        return get_routing_distance(p1.coordinate, p2.coordinate, routing_type), []
        
    path_doors = bfs_room_path(p1.room_name, p2.room_name, doors)
    
    if not path_doors:
        # Fallback to direct if disconnected
        return get_routing_distance(p1.coordinate, p2.coordinate, routing_type), []
        
    # Calculate total distance: P1 -> Door1 -> Door2 ... -> P2
    total_dist = 0.0
    curr_coord = p1.coordinate
    
    transit_z = 2.8 if routing_type == 'ceiling' else 0.0
    waypoints = []
    
    for d in path_doors:
        # Move to door transit point
        # Use door center, but adjust Z
        d_coord = Coordinate(d.coordinate.x, d.coordinate.y, transit_z)
        waypoints.append(d_coord)
        
        total_dist += get_routing_distance(curr_coord, d_coord, routing_type)
        curr_coord = d_coord
        
    # Final leg
    total_dist += get_routing_distance(curr_coord, p2.coordinate, routing_type)
    return total_dist, waypoints

def build_topology(rooms: List[Room], points: List[Point], doors: List[Door] = None) -> Topology:
    if doors is None: doors = []
    edges: List[Edge] = []
    
    # --- 1. Identify Trunks ---
    db_point = next((p for p in points if p.subtype == 'db_box'), None)
    elv_point = next((p for p in points if p.subtype == 'elv_box'), None)
    water_point = next((p for p in points if p.subtype == 'manifold'), None)

    # --- 2. Lighting Circuit (Ceiling, Daisy Chain) ---
    lights = [p for p in points if p.subtype == 'light']
    switches = [p for p in points if p.subtype == 'switch']
    
    if lights and db_point:
        unvisited = lights.copy()
        curr = db_point
        curr_id = db_point.id
        
        while unvisited:
            # Find nearest reachable light
            def get_dist(l):
                d, _ = get_path_distance(curr, l, doors, 'ceiling')
                return d
            
            nearest = min(unvisited, key=get_dist)
            
            dist, wps = get_path_distance(curr, nearest, doors, 'ceiling')
            edges.append(Edge(a=curr_id, b=nearest.id, weight=dist, kind='trunk', routing_type='ceiling', waypoints=wps, circuit_id='L1'))
            
            curr = nearest
            curr_id = nearest.id
            unvisited.remove(nearest)
            
    # Connect Switches to Lights (Branch)
    for sw in switches:
        # Connect to light in same room
        local_lights = [l for l in lights if l.room_name == sw.room_name]
        if local_lights:
            target = min(local_lights, key=lambda l: get_routing_distance(sw.coordinate, l.coordinate, 'ceiling'))
            dist = get_routing_distance(sw.coordinate, target.coordinate, 'ceiling')
            # Switch leg usually goes up wall then ceiling. No cross-room, so no waypoints needed usually.
            edges.append(Edge(a=target.id, b=sw.id, weight=dist, kind='branch', routing_type='wall', circuit_id='L1'))
            
    # --- 3. Socket Circuit (Floor) ---
    sockets = [p for p in points if p.subtype == 'socket'] # General sockets
    
    # Identify Kitchen Sockets
    kitchen_sockets = [s for s in sockets if '厨房' in s.room_name or 'Kitchen' in s.room_name]
    normal_sockets = [s for s in sockets if s not in kitchen_sockets]
    
    # 3.1 Kitchen (Home Run - High Power)
    if db_point:
        for idx, ks in enumerate(kitchen_sockets):
            dist, wps = get_path_distance(db_point, ks, doors, 'floor')
            cid = f'K{idx+1}'
            edges.append(Edge(a=db_point.id, b=ks.id, weight=dist, kind='trunk', routing_type='floor', waypoints=wps, circuit_id=cid))

    # 3.2 Normal Rooms (Independent Circuit per Room, Daisy Chain inside)
    room_sockets = collections.defaultdict(list)
    for s in normal_sockets:
        room_sockets[s.room_name].append(s)
        
    if db_point:
        c_idx = 1
        for room, room_s_list in room_sockets.items():
            if not room_s_list: continue
            
            cid = f'C{c_idx}' # C for Circuit/Common
            c_idx += 1
            
            unvisited = room_s_list.copy()
            
            # Helper to find closest to P
            def get_dist_to_p(s, target_p):
                d, _ = get_path_distance(target_p, s, doors, 'floor')
                return d
            
            # Start of chain (closest to DB)
            start_socket = min(unvisited, key=lambda s: get_dist_to_p(s, db_point))
            
            # Connect DB -> Start
            dist, wps = get_path_distance(db_point, start_socket, doors, 'floor')
            edges.append(Edge(a=db_point.id, b=start_socket.id, weight=dist, kind='trunk', routing_type='floor', waypoints=wps, circuit_id=cid))
            
            unvisited.remove(start_socket)
            curr = start_socket
            
            # Chain the rest
            while unvisited:
                # Nearest neighbor from CURRENT socket
                nearest = min(unvisited, key=lambda s: get_dist_to_p(s, curr))
                
                dist, wps = get_path_distance(curr, nearest, doors, 'floor')
                edges.append(Edge(a=curr.id, b=nearest.id, weight=dist, kind='trunk', routing_type='floor', waypoints=wps, circuit_id=cid))
                
                curr = nearest
                unvisited.remove(nearest)

    # --- 4. AC Circuits (Direct Home Run) ---
    ac_sockets = [p for p in points if p.subtype == 'socket_ac']
    if db_point:
        for idx, ac in enumerate(ac_sockets):
            dist, wps = get_path_distance(db_point, ac, doors, 'floor') 
            cid = f'AC{idx+1}'
            edges.append(Edge(a=db_point.id, b=ac.id, weight=dist, kind='trunk', routing_type='floor', waypoints=wps, circuit_id=cid))

    # --- 5. Weak Electric (Direct Home Run from ELV Box) ---
    weak_points = [p for p in points if p.system == 'weak_electric' and p.subtype != 'elv_box']
    if elv_point:
        for wp in weak_points:
            dist, wps = get_path_distance(elv_point, wp, doors, 'floor')
            edges.append(Edge(a=elv_point.id, b=wp.id, weight=dist, kind='trunk', routing_type='floor', waypoints=wps, circuit_id='WE'))

    # --- 6. Water Supply (Direct Home Run from Manifold) ---
    # BS_design: "从分水器沿顶棚→墙面垂直下降" (Ceiling Routing)
    water_targets = [p for p in points if p.system == 'water_supply' and p.subtype != 'manifold']
    if water_point:
        for wp in water_targets:
            dist, wps = get_path_distance(water_point, wp, doors, 'ceiling')
            edges.append(Edge(a=water_point.id, b=wp.id, weight=dist, kind='trunk', routing_type='ceiling', waypoints=wps, circuit_id='WS'))
            
    # Drainage (Simplified: Direct to nearest drain stack or floor drain)
    # We didn't model stacks, so skip or link to self.
            
    return Topology(points=points, edges=edges, doors=doors)
