"""
Data structure for a single annotation.
"""
import dataclasses

@dataclasses.dataclass
class Annotation:
    """
    Represents a single annotation.
    """
    id: int
    image_id: int
    label: str
    points: list[tuple[int, int]]
