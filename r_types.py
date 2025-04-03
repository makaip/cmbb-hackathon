import enum
from pydantic import BaseModel, Field
from typing import List
class RelationType(enum.Enum):
    BP = 'Biological Process'
    MF = 'Molecular Function'
    CC = 'Cellular Component'
    RS = 'Research Studies'

class Relationship(BaseModel):
    gene_ids: List[str]  # Simple default empty list
    description: str
    relation_type: RelationType  # Required field without using Field