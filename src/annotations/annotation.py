"""
Data structure for a single annotation.
"""
import dataclasses

@dataclasses.dataclass
class Annotation:
    """
    Represents a single annotation in YOLO format.
    """
    id: int
    image_id: int
    class_id: int
    bbox: list[float]
