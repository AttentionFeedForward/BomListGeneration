from typing import Dict, List, Any
from mep_semantics import Topology, Point

def aggregate_lengths(topology: Topology) -> Dict[str, Dict[str, float]]:
    """
    Aggregates edge lengths by system and kind.
    Returns: {
        'strong_electric': {'trunk': 0.0, 'branch': 0.0},
        'weak_electric': {'trunk': 0.0},
        'water_supply': {'trunk': 0.0},
        'drainage': {'trunk': 0.0}
    }
    """
    res = {
        'strong_electric': {'trunk': 0.0, 'branch': 0.0},
        'weak_electric': {'trunk': 0.0, 'branch': 0.0},
        'water_supply': {'trunk': 0.0, 'branch': 0.0},
        'drainage': {'trunk': 0.0, 'branch': 0.0}
    }
    
    point_map = {p.id: p for p in topology.points}
    
    for e in topology.edges:
        p_a = point_map.get(e.a)
        if not p_a:
            continue
            
        # Determine system
        sys_cat = 'strong_electric' # default
        
        # Check system attribute first
        if p_a.system == 'water_supply':
            sys_cat = 'water_supply'
        elif p_a.system == 'drainage':
            sys_cat = 'drainage'
        elif p_a.system == 'weak_electric':
            sys_cat = 'weak_electric'
        elif p_a.system == 'strong_electric':
            sys_cat = 'strong_electric'
        else:
            # Fallback by subtype
            if p_a.subtype in ['light', 'switch', 'socket', 'socket_ac', 'db_box']:
                sys_cat = 'strong_electric'
            elif p_a.subtype in ['elv_box', 'data', 'tv', 'net_socket']:
                sys_cat = 'weak_electric'
            elif p_a.subtype in ['manifold', 'water_point']:
                sys_cat = 'water_supply'
            elif p_a.subtype in ['floor_drain', 'toilet', 'sewer', 'drain_point']:
                sys_cat = 'drainage'
        
        kind = e.kind if e.kind in ['trunk', 'branch'] else 'trunk'
        res[sys_cat][kind] += e.weight
        
    return res

def count_boxes(points: List[Point], subtypes: List[str]) -> int:
    return sum(1 for p in points if p.subtype in subtypes)

def material_breakdown(bs: Dict[str, Any], project_type: str, room_type: str, topology: Topology) -> List[Dict[str, Any]]:
    res: List[Dict[str, Any]] = []
    
    # 1. Calculate Lengths
    lengths = aggregate_lengths(topology)
    
    # --- Helper to push items ---
    def push(name: str, qty: float, unit: str, spec: str, code: str, formula: str, category: str = 'electrical'):
        if qty <= 0: return
        res.append({
            'name': name,
            'specification': spec,
            'quantity': round(qty, 2) if unit != '个' else int(round(qty)),
            'unit': unit,
            'category': category,
            'layer_type': '机电安装',
            'material_code': code,
            'calculation_formula': formula
        })

    # ==========================================
    # 1. Strong Electric (强电)
    # ==========================================
    se_len = lengths['strong_electric']['trunk'] + lengths['strong_electric']['branch']
    se_fixtures = bs.get('electrical_system', {}).get('strong_electric', {})
    se_devices = bs.get('electrical_system', {}).get('electrical_fixtures', {})
    
    # 1.1 Conduits (Pipes)
    pipe = se_fixtures.get('电工管', {})
    if pipe:
        push('电工管', se_len, 'm', pipe.get('规格', ''), pipe.get('code', ''), f'配线路径长度 {se_len:.2f}m')
        
    # 1.2 Fittings (Elbows/Connectors)
    elbow = se_fixtures.get('电工管弯头', {})
    if elbow:
        push('电工管弯头', se_len / 5.0, elbow.get('unit', '个'), elbow.get('规格', ''), elbow.get('code', ''), f'L/5')
    conn = se_fixtures.get('电工管直通', {})
    if conn:
        push('电工管直通', se_len / 3.0, conn.get('unit', '个'), conn.get('规格', ''), conn.get('code', ''), f'L/3')
        
    # 1.3 Boxes (底盒)
    # Count switches, sockets
    box_count = count_boxes(topology.points, ['switch', 'socket', 'socket_ac'])
    box_item = se_devices.get('底盒', {})
    if box_item:
        push('底盒', box_count, box_item.get('unit', '个'), box_item.get('规格', ''), box_item.get('code', ''), f'点位数量 {box_count}')
        
    # 1.4 Cups (杯梳)
    cup = se_devices.get('杯梳', {})
    if cup:
        # Simplified logic: 2 per box? Or use the indicator logic from before
        # Using simplified constant 2 per box for stability, or re-implement complex logic if needed.
        # Let's stick to the previous indicator logic if possible, but for now simple is robust.
        # The previous code had complex dict lookup. Let's simplify: usually 1-2 per box.
        push('杯梳', box_count * 1.5, '个', cup.get('规格', ''), cup.get('code', ''), f'1.5 × 底盒数')

    # 1.5 Wires (Simplified estimation based on pipe length)
    # Usually 3 wires (L,N,PE) per pipe.
    wire_light = se_fixtures.get('照明回路线', {})
    if wire_light:
        # Estimate: 30% of pipe is lighting? Or better: if we knew which edges were lighting.
        # For now, just a rough factor of total pipe.
        # Better: We assume 3 wires in conduit.
        push('BV-2.5mm²电线', se_len * 3, 'm', wire_light.get('规格', ''), wire_light.get('code', ''), f'3 × 管长')

    # ==========================================
    # 2. Weak Electric (弱电)
    # ==========================================
    we_len = lengths['weak_electric']['trunk']
    we_fixtures = bs.get('electrical_system', {}).get('weak_electric', {})
    
    # 2.1 Conduits
    elv_pipe = we_fixtures.get('弱电管', {})
    if elv_pipe:
        push('弱电管', we_len, 'm', elv_pipe.get('规格', ''), elv_pipe.get('code', ''), f'弱电路径 {we_len:.2f}m', 'weak_electric')
    
    # 2.2 Cables (CAT6 / Coax)
    # We don't distinguish CAT6 vs TV edges in aggregate_lengths easily yet.
    # Assume 80% data, 20% TV or just sum them?
    # Let's just output CAT6 for the full length for now as a baseline.
    cat6 = we_fixtures.get('网线', {})
    if cat6:
        push('网线', we_len * 1.1, 'm', cat6.get('规格', ''), cat6.get('code', ''), f'1.1 × 管长', 'weak_electric')

    # ==========================================
    # 3. Plumbing (Water Supply)
    # ==========================================
    ws_len = lengths['water_supply']['trunk']
    plumbing = bs.get('plumbing_system', {})
    
    # 3.1 PPR Pipe
    ppr = plumbing.get('PPR给水管', {})
    if ppr:
        push('PPR给水管', ws_len, 'm', ppr.get('规格', ''), ppr.get('code', ''), f'给水路径 {ws_len:.2f}m', 'plumbing')
        
    # 3.2 Valves (One per water point + 1 main)
    water_points = count_boxes(topology.points, ['water_point'])
    valve = plumbing.get('阀门', {})
    if valve:
        push('阀门', water_points + 1, '个', valve.get('规格', ''), valve.get('code', ''), f'点位 {water_points} + 1总阀', 'plumbing')

    # ==========================================
    # 4. Plumbing (Drainage)
    # ==========================================
    # We don't have drainage edges yet, so we estimate.
    # Estimate: 2.5m per drain point (vertical drop + connection)
    # Drainage points = Floor Drains + Water Points (Sinks, Toilets, etc. imply drainage)
    floor_drains = count_boxes(topology.points, ['drain_point'])
    total_drain_spots = floor_drains + water_points
    
    est_drain_len = total_drain_spots * 2.5 
    
    drain_pipe = plumbing.get('PVC-U排水管', {})
    if drain_pipe and total_drain_spots > 0:
        push('PVC-U排水管', est_drain_len, 'm', drain_pipe.get('规格', ''), drain_pipe.get('code', ''), f'估算: {total_drain_spots}点 × 2.5m', 'plumbing')

    return res
