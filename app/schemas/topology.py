from typing import List, Optional

from pydantic import BaseModel


class TopologyNode(BaseModel):
    name: str
    type: str
    ip: Optional[str] = None
    status: Optional[str] = None
    kapasitas: Optional[str] = None
    children: List["TopologyNode"] = []


# Ini memungkinkan model untuk mereferensikan dirinya sendiri (untuk 'children')
TopologyNode.model_rebuild()
