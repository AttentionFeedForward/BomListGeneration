import math
from typing import List, Dict, Tuple
from mep_semantics import Room, Point, Coordinate, Door

def solve_rect_dimensions(area: float, perimeter: float):
    p_half = perimeter / 2.0
    discriminant = p_half**2 - 4 * area
    if discriminant < 0:
        s = math.sqrt(area)
        return s, s
    sqrt_d = math.sqrt(discriminant)
    w = (p_half + sqrt_d) / 2.0
    d = (p_half - sqrt_d) / 2.0
    return w, d

def get_polygon_centroid(poly: List[Dict[str, float]]) -> Coordinate:
    if not poly: return Coordinate(0,0,0)
    x = sum(p['x'] for p in poly) / len(poly)
    y = sum(p['y'] for p in poly) / len(poly)
    return Coordinate(x, y, 0)

def closest_point_on_segment(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0: return x1, y1
    
    t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
    t = max(0, min(1, t))
    return x1 + t * dx, y1 + t * dy

def snap_to_polygon_wall(poly: List[Dict[str, float]], ideal_x: float, ideal_y: float) -> Tuple[float, float]:
    best_x, best_y = ideal_x, ideal_y
    min_dist = float('inf')
    
    for i in range(len(poly)):
        p1 = poly[i]
        p2 = poly[(i+1) % len(poly)]
        
        cx, cy = closest_point_on_segment(ideal_x, ideal_y, p1['x'], p1['y'], p2['x'], p2['y'])
        dist = (cx - ideal_x)**2 + (cy - ideal_y)**2
        
        if dist < min_dist:
            min_dist = dist
            best_x, best_y = cx, cy
            
    return best_x, best_y

def assign_coordinates_and_layout(rooms: List[Room], points: List[Point]) -> List[Door]:
    doors: List[Door] = []
    
    # 1. Determine Room Dimensions
    for r in rooms:
        w, d = solve_rect_dimensions(r.area, r.perimeter)
        r.dims = (w, d)
        if not r.origin:
             r.origin = Coordinate(0, 0, 0)

    # 2. Layout (Skip if origins are already set by JSON/Test)
    if all(r.origin.x == 0 and r.origin.y == 0 for r in rooms) and len(rooms) > 1:
        # Simple layout strategy (Hub-Spoke)
        lr = next((r for r in rooms if r.room_type == '客厅'), rooms[0])
        lr.origin = Coordinate(0, 0, 0)
        current_x = lr.dims[0]
        for r in rooms:
            if r == lr: continue
            r.origin = Coordinate(current_x, 0, 0)
            current_x += r.dims[0]
            
    # 3. Create Doors
    # Logic: If doors are not pre-defined, create logical doors.
    # If we have polygons, we could infer adjacency, but for now we stick to the Hub-Spoke logical connectivity
    # unless 'final_analysis.json' provided better info.
    # The current engine relies on `mep_layout` to MAKE doors.
    
    living_room = next((r for r in rooms if r.room_type == '客厅'), None)
    
    if living_room:
        for r in rooms:
            if r == living_room: continue
            
            # Find best door position
            # If we have polygons, use centroid path intersection with boundary
            # Else use bounding box logic
            
            door_pos = Coordinate(0,0,0)
            
            if r.polygon and living_room.polygon:
                # Find closest segments between two polygons?
                # Simplified: Midpoint of centroids, snapped to shared boundary?
                # Or just use the bounding box logic as a fallback for logical connectivity
                # But we want visual accuracy.
                
                # Let's find the point on R's boundary closest to LR's centroid
                lr_center = get_polygon_centroid(living_room.polygon)
                r_center = get_polygon_centroid(r.polygon)
                
                # Door on R's side
                dx, dy = snap_to_polygon_wall(r.polygon, lr_center.x, lr_center.y)
                # Ideally, we check if this point is close to LR.
                # For now, just place it there.
                door_pos = Coordinate(dx, dy, 0)
                
            else:
                # Bounding Box Logic
                lr_ox, lr_oy = living_room.origin.x, living_room.origin.y
                lr_w, lr_d = living_room.dims
                
                c1 = (lr_ox + lr_w/2, lr_oy + lr_d/2)
                c2 = (r.origin.x + r.dims[0]/2, r.origin.y + r.dims[1]/2)
                
                dx = c2[0] - c1[0]
                dy = c2[1] - c1[1]
                
                if abs(dx) > abs(dy):
                    if dx > 0: # R is right
                        door_pos = Coordinate(r.origin.x, r.origin.y + r.dims[1]/2, 0)
                    else: # R is left
                        door_pos = Coordinate(r.origin.x + r.dims[0], r.origin.y + r.dims[1]/2, 0)
                else:
                    if dy > 0: # R is below
                        door_pos = Coordinate(r.origin.x + r.dims[0]/2, r.origin.y, 0)
                    else: # R is above
                        door_pos = Coordinate(r.origin.x + r.dims[0]/2, r.origin.y + r.dims[1], 0)
            
            doors.append(Door(room_a=living_room.name, room_b=r.name, coordinate=door_pos))

    # 4. Place Points
    room_points: Dict[str, List[Point]] = {}
    for p in points:
        room_points.setdefault(p.room_name, []).append(p)

    for r in rooms:
        pts = room_points.get(r.name, [])
        ox, oy = r.origin.x, r.origin.y
        w, d = r.dims
        
        # Door position for "near_door" logic
        my_door = next((dr for dr in doors if dr.room_a == r.name or dr.room_b == r.name), None)
        door_x, door_y = ox, oy # Default
        if my_door and my_door.coordinate:
            door_x, door_y = my_door.coordinate.x, my_door.coordinate.y

        has_poly = len(r.polygon) > 0
        
        for p in pts:
            z = 0.3
            
            # --- Z-Height ---
            if 'ceiling' in p.anchor: z = 2.8
            elif 'bedside' in p.anchor: z = 0.7
            elif 'desk' in p.anchor: z = 1.0
            elif 'counter_top' in p.anchor: z = 1.1
            elif 'switch' in p.subtype: z = 1.3
            elif 'ac_position' in p.anchor: z = 2.2
            elif 'washing_machine' in p.anchor: z = 1.2
            elif 'water_heater' in p.anchor: z = 1.6
            elif 'shower' in p.anchor: z = 1.0
            elif 'toilet' in p.anchor: z = 0.3
            elif 'basin' in p.anchor: z = 0.5
            elif 'manifold' in p.subtype: z = 0.5
            
            # --- XY Position ---
            
            # 1. Ceiling (Center)
            if 'ceiling' in p.anchor:
                if has_poly:
                    c = get_polygon_centroid(r.polygon)
                    p.coordinate = Coordinate(c.x, c.y, z)
                else:
                    p.coordinate = Coordinate(ox + w/2, oy + d/2, z)
                continue

            # 2. Near Door (Switch)
            if 'near_door' in p.anchor or 'entrance' in p.anchor:
                # Place near the door
                # If polygon, find point on wall near door
                ideal_x, ideal_y = door_x, door_y
                # Slight offset to avoid being ON the door?
                # For now, just use door position, maybe offset slightly towards room center?
                # Actually, switches are ON the wall next to door.
                # Just use door pos for now, or snap to nearest wall point slightly away?
                p.coordinate = Coordinate(door_x, door_y, z)
                continue

            # 3. Wall Anchors (TV, Sofa, Bed, etc.)
            # Determine "Ideal" logical position relative to bounding box
            ideal_x, ideal_y = ox + w/2, oy + d/2 # Default center
            
            if 'tv_wall' in p.anchor:
                # Top wall usually
                ideal_x = ox + w/2
                ideal_y = oy # Top
            elif 'sofa' in p.anchor:
                # Bottom wall
                ideal_x = ox + w/2
                ideal_y = oy + d # Bottom
            elif 'bedside' in p.anchor:
                # Top wall
                ideal_x = ox + w/2
                ideal_y = oy
                if 'left' in p.anchor: ideal_x -= 1.0
                if 'right' in p.anchor: ideal_x += 1.0
            elif 'desk' in p.anchor:
                ideal_x = ox + w - 0.1
                ideal_y = oy + d/2
            elif 'counter_top' in p.anchor:
                ideal_x = ox + 0.1
                ideal_y = oy + d/2
            elif 'toilet' in p.anchor:
                ideal_x = ox + w
                ideal_y = oy + d/2
            elif 'basin' in p.anchor:
                ideal_x = ox
                ideal_y = oy + d/2
            elif 'shower' in p.anchor:
                ideal_x = ox + w
                ideal_y = oy
            elif 'sink' in p.anchor:
                ideal_x = ox
                ideal_y = oy + d/2
            elif 'washing_machine' in p.anchor:
                ideal_x = ox
                ideal_y = oy + d - 0.5
            elif 'water_heater' in p.anchor:
                ideal_x = ox + w/3
                ideal_y = oy
            elif 'dry_area_wall' in p.anchor:
                ideal_x = door_x + 0.5
                ideal_y = door_y
            elif 'floor_drain' in p.anchor:
                # Floor drain - use centroid for now (z=0)
                if has_poly:
                    c = get_polygon_centroid(r.polygon)
                    p.coordinate = Coordinate(c.x, c.y, 0)
                else:
                    p.coordinate = Coordinate(ox + w/2, oy + d/2, 0)
                continue
            
            # Snap to Polygon Wall
            if has_poly:
                # Determine "Side" based on bounding box relation
                # If ideal is "Top", it means min Y.
                # Instead of hardcoding ideal coords, let's use the bbox relative position
                # and snap to the polygon.
                
                # Re-calculate ideal based on bbox
                # BBox is ox, oy, w, d
                
                # Use the logic above to set ideal_x/y on the bbox, then snap.
                # But bbox might be loose.
                # Let's trust the snap function.
                
                # Correct "Top" is min Y in graphics usually? 
                # In standard coords, usually Y goes up? 
                # Floorplan pixels: Y goes down (usually). 
                # Let's assume standard image coords: (0,0) top-left.
                # So "Top" wall is min_y. "Bottom" is max_y.
                
                # The logic above: 
                # Top = oy (min y) -> Correct for image coords
                # Bottom = oy + d (max y) -> Correct
                
                sx, sy = snap_to_polygon_wall(r.polygon, ideal_x, ideal_y)
                p.coordinate = Coordinate(sx, sy, z)
            else:
                p.coordinate = Coordinate(ideal_x, ideal_y, z)

    return doors
