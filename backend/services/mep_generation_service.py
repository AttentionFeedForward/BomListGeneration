import sys
import os
from typing import Dict, Any

backend_path = os.path.dirname(os.path.dirname(__file__))
project_path = os.path.dirname(backend_path)
modules_path = os.path.join(project_path, 'llm', 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

import mep_engine

class MEPGenerationService:
    def generate(self, floorplan_data: Dict[str, Any], project_type: str = '住宅') -> Dict[str, Any]:
        return mep_engine.generate(floorplan_data, project_type)

