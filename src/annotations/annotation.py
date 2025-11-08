"""
Data structure for a single annotation.
"""
import dataclasses

@dataclasses.dataclass
class Annotation:
    """
    Represents a single annotation with bounding box coordinates in x1, y1, x2, y2 format.
    Coordinates are normalized (0.0 to 1.0).
    """
    id: int
    image_id: int
    class_id: int
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_yolo(cls, id: int, image_id: int, class_id: int, bbox_yolo: list[float]):
        """
        Creates an Annotation object from YOLO format (x_center, y_center, width, height).
        """
        x_center, y_center, width, height = bbox_yolo
        x1 = x_center - (width / 2)
        y1 = y_center - (height / 2)
        x2 = x_center + (width / 2)
        y2 = y_center + (height / 2)
        return cls(id=id, image_id=image_id, class_id=class_id, x1=x1, y1=y1, x2=x2, y2=y2)

    def to_yolo(self) -> list[float]:
        """
        Converts the current x1, y1, x2, y2 format to YOLO format (x_center, y_center, width, height).
        """
        width = self.x2 - self.x1
        height = self.y2 - self.y1
        x_center = self.x1 + (width / 2)
        y_center = self.y1 + (height / 2)
        return [x_center, y_center, width, height]

    def to_x1y1x2y2(self) -> list[float]:
        """
        Returns the bounding box coordinates in x1, y1, x2, y2 format.
        """
        return [self.x1, self.y1, self.x2, self.y2]
