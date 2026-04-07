from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class RoomInput:
    name: str
    room_type: str
    area: float
    perimeter: float
    wall_lengths: List[float]
    doors_length: float
    windows_length: float
    practices: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Coordinate:
    x: float
    y: float
    z: float

@dataclass
class Door:
    room_a: str
    room_b: str
    width: float = 0.8
    coordinate: Optional[Coordinate] = None # Center of door in global coords

@dataclass
class Room:
    name: str
    room_type: str
    area: float
    perimeter: float
    wall_lengths: List[float]
    doors_length: float
    windows_length: float
    neighbors: List[str] = field(default_factory=list)
    origin: Optional[Coordinate] = None # Global offset (x,y,0)
    dims: tuple = (0, 0) # w, d
    polygon: List[Dict[str, float]] = field(default_factory=list) # [{'x':.., 'y':..}, ...]

@dataclass
class Point:
    id: str
    system: str
    subtype: str
    room_name: str
    anchor: str
    coordinate: Optional[Coordinate] = None
    is_fixed: bool = False # If true, manual adjustment needed, but we auto-place

@dataclass
class Edge:
    a: str
    b: str
    weight: float
    kind: str # trunk(main), branch(switch leg), vertical(drop)
    routing_type: str = 'floor' # floor, ceiling, wall
    waypoints: List[Coordinate] = field(default_factory=list)
    circuit_id: str = '' # e.g., 'C1', 'K1', 'AC1'

@dataclass
class Topology:
    points: List[Point]
    edges: List[Edge]
    doors: List[Door] = field(default_factory=list)

def build_rooms(inputs: List[Dict[str, Any]]) -> List[Room]:
    rooms: List[Room] = []
    for i, r in enumerate(inputs):
        # Allow pre-set dimensions if available (from test)
        # We need to handle 'origin' input from test dict if present
        origin_dict = r.get('origin', {})
        origin = None
        if origin_dict:
            origin = Coordinate(x=float(origin_dict.get('x', 0)), y=float(origin_dict.get('y', 0)), z=0)
            
        room = Room(
            name=r.get('name', f'房间{i+1}'),
            room_type=r.get('room_type', '其余'),
            area=float(r.get('area', 0) or 0),
            perimeter=float(r.get('perimeter', 0) or 0),
            wall_lengths=list(r.get('wall_lengths', []) or []),
            doors_length=float(r.get('doors_length', 0) or 0),
            windows_length=float(r.get('windows_length', 0) or 0),
            neighbors=[],
            origin=origin,
            polygon=r.get('polygon', [])
        )
        rooms.append(room)
    return rooms
