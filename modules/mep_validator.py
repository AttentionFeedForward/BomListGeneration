from typing import Dict, Any, List

def deviation_check(bs: Dict[str, Any], project_type: str, room_area: float, computed_pipe_len: float) -> Dict[str, Any]:
    item = bs.get('electrical_system', {}).get('strong_electric', {}).get('电工管', {})
    val = item.get(project_type, 0)
    base = 0.0
    if isinstance(val, (int, float)):
        base = float(val) * float(room_area or 0)
    return {
        'metric': '电工管长度',
        'expected': round(base, 2),
        'actual': round(computed_pipe_len, 2),
        'deviation': round(computed_pipe_len - base, 2)
    }

def rules_check(min_counts: Dict[str, int], actual_counts: Dict[str, int]) -> List[Dict[str, Any]]:
    res: List[Dict[str, Any]] = []
    for k, v in min_counts.items():
        act = int(actual_counts.get(k, 0))
        ok = act >= v
        res.append({'item': k, 'min_required': v, 'actual': act, 'pass': ok})
    return res

