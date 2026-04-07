from typing import List, Dict
from mep_semantics import Room, Point

def place_points(rooms: List[Room], project_type: str, counts_by_room: Dict[str, Dict[str, int]]) -> List[Point]:
    points: List[Point] = []
    idx = 1
    
    # Helper to find specific room types
    living_room = next((r for r in rooms if r.room_type == '客厅'), None)
    
    # 1. TRUNK EQUIPMENT (Placed once)
    # Strong/Weak Box -> Entrance (Living Room)
    if living_room:
        points.append(Point(id='DB-MAIN', system='electrical', subtype='db_box', room_name=living_room.name, anchor='entrance_wall'))
        points.append(Point(id='ELV-MAIN', system='weak_electric', subtype='elv_box', room_name=living_room.name, anchor='entrance_wall_offset'))
    
    # Water Manifold -> Bathroom Dry Area (First bathroom found)
    bathroom = next((r for r in rooms if r.room_type == '卫生间'), None)
    if bathroom:
        points.append(Point(id='WATER-MANIFOLD', system='water_supply', subtype='manifold', room_name=bathroom.name, anchor='dry_area_wall'))

    for room in rooms:
        counts = counts_by_room.get(room.name, {})
        r_type = room.room_type
        
        # --- LIGHTING ---
        if counts.get('照明灯具', 0) > 0:
             points.append(Point(id=f'LIGHT-{idx}', system='electrical', subtype='light', room_name=room.name, anchor='ceiling_center'))
             idx += 1
        
        # --- SWITCHES ---
        # Rule: All rooms have main switch near door
        # Kitchen/Bath: Outside door (logically belongs to room, physically outside) -> 'near_door_outside'
        # Living/Bedroom: Inside door -> 'near_door_inside'
        switch_anchor = 'near_door_outside' if r_type in ['厨房', '卫生间'] else 'near_door_inside'
        points.append(Point(id=f'SW-MAIN-{idx}', system='electrical', subtype='switch', room_name=room.name, anchor=switch_anchor))
        idx += 1
        
        # Dual Control (Living/Bedroom)
        if r_type == '客厅':
            points.append(Point(id=f'SW-DUAL-{idx}', system='electrical', subtype='switch', room_name=room.name, anchor='sofa_side'))
            idx += 1
        elif r_type == '卧室':
            points.append(Point(id=f'SW-DUAL-{idx}', system='electrical', subtype='switch', room_name=room.name, anchor='bedside'))
            idx += 1
            
        # --- SOCKETS ---
        # AC Socket (Split Unit) - Living/Bedroom
        if r_type in ['客厅', '卧室']:
             points.append(Point(id=f'SKT-AC-{idx}', system='electrical', subtype='socket_ac', room_name=room.name, anchor='ac_position'))
             idx += 1
        
        # General Sockets
        n_sockets = counts.get('插座', 0)
        # We manually placed AC, so decrement if needed, but usually we just fill the count.
        # Let's place specific functional sockets first, then fill remainder.
        
        placed_sockets = 0
        
        if r_type == '客厅':
            # TV Wall, Sofa Side x2
            points.append(Point(id=f'SKT-TV-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='tv_wall'))
            idx += 1; placed_sockets += 1
            points.append(Point(id=f'SKT-SOFA-L-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='sofa_side_left'))
            idx += 1; placed_sockets += 1
            points.append(Point(id=f'SKT-SOFA-R-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='sofa_side_right'))
            idx += 1; placed_sockets += 1
            
        elif r_type == '卧室':
            # Bedside x2, TV/Desk
            points.append(Point(id=f'SKT-BED-L-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='bedside_left'))
            idx += 1; placed_sockets += 1
            points.append(Point(id=f'SKT-BED-R-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='bedside_right'))
            idx += 1; placed_sockets += 1
            points.append(Point(id=f'SKT-DESK-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='study_desk'))
            idx += 1; placed_sockets += 1
            
        elif r_type == '厨房':
            # Countertop x3 (Fridge, Microwave, General)
            for k in range(3):
                points.append(Point(id=f'SKT-KIT-{k}-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='counter_top'))
                idx += 1; placed_sockets += 1
                
        elif r_type == '卫生间':
            # Toilet, Basin, Washing Machine
            points.append(Point(id=f'SKT-TOILET-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='toilet_side'))
            idx += 1; placed_sockets += 1
            points.append(Point(id=f'SKT-BASIN-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='basin_side'))
            idx += 1; placed_sockets += 1
        
        # Fill remaining sockets evenly
        remaining = max(0, n_sockets - placed_sockets)
        for j in range(remaining):
            points.append(Point(id=f'SKT-GEN-{idx}', system='electrical', subtype='socket', room_name=room.name, anchor='general_wall'))
            idx += 1

        # --- WEAK ELECTRIC ---
        if r_type == '客厅':
             points.append(Point(id=f'NET-TV-{idx}', system='weak_electric', subtype='net_socket', room_name=room.name, anchor='tv_wall'))
             idx += 1
        elif r_type == '书房' or (r_type == '卧室' and counts.get('网络', 0) > 0):
             points.append(Point(id=f'NET-DESK-{idx}', system='weak_electric', subtype='net_socket', room_name=room.name, anchor='study_desk'))
             idx += 1
             
        # --- WATER POINTS (Inferred from room type for now) ---
        if r_type == '卫生间':
            points.append(Point(id=f'WATER-BASIN-{idx}', system='water_supply', subtype='water_point', room_name=room.name, anchor='basin'))
            idx += 1
            points.append(Point(id=f'WATER-SHOWER-{idx}', system='water_supply', subtype='water_point', room_name=room.name, anchor='shower'))
            idx += 1
            points.append(Point(id=f'WATER-TOILET-{idx}', system='water_supply', subtype='water_point', room_name=room.name, anchor='toilet'))
            idx += 1
            points.append(Point(id=f'WATER-WASH-{idx}', system='water_supply', subtype='water_point', room_name=room.name, anchor='washing_machine'))
            idx += 1
            # Drainage
            points.append(Point(id=f'DRAIN-FLOOR-{idx}', system='drainage', subtype='drain_point', room_name=room.name, anchor='floor_drain_center'))
            idx += 1
        elif r_type == '厨房':
            points.append(Point(id=f'WATER-SINK-{idx}', system='water_supply', subtype='water_point', room_name=room.name, anchor='sink'))
            idx += 1
            points.append(Point(id=f'WATER-HEATER-{idx}', system='water_supply', subtype='water_point', room_name=room.name, anchor='water_heater'))
            idx += 1

    return points
