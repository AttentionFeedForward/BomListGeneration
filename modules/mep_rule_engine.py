import json
import os
from typing import Dict, Any, List

def load_bs() -> Dict[str, Any]:
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, 'BS.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def room_key(room_type: str) -> str:
    if room_type in ['客厅', '卧室', '厨房', '卫生间']:
        return room_type
    return '其余'

def min_fixture_counts(bs: Dict[str, Any], project_type: str, room_type: str) -> Dict[str, int]:
    fixtures = bs.get('electrical_system', {}).get('electrical_fixtures', {})
    res: Dict[str, int] = {}
    def pick(name: str) -> int:
        item = fixtures.get(name)
        if not item:
            return 0
        val = item.get(project_type)
        if isinstance(val, dict):
            return int(val.get(room_key(room_type), val.get('其余', 0)) or 0)
        if isinstance(val, (int, float)):
            return int(val)
        return 0
    res['配电箱'] = pick('配电箱')
    res['弱电箱'] = pick('弱电箱')
    res['照明灯具'] = pick('照明灯具')
    res['开关'] = pick('开关')
    res['插座'] = pick('插座')
    res['底盒'] = pick('底盒')
    return res

