from typing import List, Tuple, Union, Optional
import cv2


# -----------------------------
# Utils / colors
# -----------------------------
colors = {
    "red":     (0, 0, 255),
    "green":   (0, 255, 0),
    "blue":    (255, 0, 0),
    "yellow":  (0, 255, 255),
    "cyan":    (255, 255, 0),
    "magenta": (255, 0, 255),
    "white":   (255, 255, 255),
    "black":   (0, 0, 0),
    "gray":    (120, 120, 120),
    "dark":    (45, 45, 45),
    "orange":  (0, 165, 255),
    "": None,
    None: None
}

class Point:
    def __init__(self, x, y, size=0, color: Union[str, Tuple[int, int, int]] = None):
        self.x = x
        self.y = y
        self.size = size
        self.color = colors[color] if type(color) == str else color

    def toTup(self):
        return (self.x, self.y)


class Line:
    def __init__(
        self,
        p1: Union[Point, Tuple[int, int]],
        p2: Union[Point, Tuple[int, int]],
        thickness=3,
        color: Union[str, Tuple[int, int, int]] = "green",
    ):
        self.p1 = p1 if type(p1) == Point else Point(*p1)
        self.p2 = p2 if type(p2) == Point else Point(*p2)
        self.thickness = thickness
        self.color = colors[color] if type(color) == str else color

    def draw(self, frame, thickness=None, color=None):
        if thickness is not None:
            self.thickness = thickness
        if color is not None:
            self.color = colors[color] if type(color) == str else color
        cv2.line(frame, self.p1.toTup(), self.p2.toTup(), self.color, self.thickness)


class ParkingSpot:
    # IMPORTANT: default list must NOT be [] (shared across instances)
    def __init__(self, id: str, lines: Optional[List[Line]] = None):
        self.id = id
        self.edges: List[Line] = lines or []
        self.full = False

    def draw(self, frame, thickness=2, color="cyan"):
        for l in self.edges:
            if self.full: color = "red"
            l.draw(frame, thickness=thickness, color=color)


class ParkingRow:
    def __init__(self, id: int, spots: Optional[List[ParkingSpot]] = None):
        self.id = id
        self.spots: List[ParkingSpot] = spots or []

    def draw(self, frame, thickness=2, color="cyan"):
        for spot in self.spots:
            spot.draw(frame, thickness=thickness, color=color)


def estimate_text_size(text: str, font_scale: float = 1.0, thickness: int = 1):
    BASE_CHAR_WIDTH = 12
    BASE_CHAR_HEIGHT = 22
    BASELINE = 8
    thickness_factor = 1 + 0.15 * (thickness - 1)
    width = int(len(text) * BASE_CHAR_WIDTH * font_scale * thickness_factor)
    height = int((BASE_CHAR_HEIGHT + BASELINE) * font_scale * thickness_factor)
    return width, height


class Button:
    def __init__(
        self,
        x, y, w, h, text,
        backgroundColor: Union[str, Tuple[int, int, int]] = "black",
        color: Union[str, Tuple[int, int, int]] = "white",
        size=0.7,
        weight=2
    ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.size = size
        self.weight = weight
        self.backgroundColor = colors[backgroundColor] if type(backgroundColor) == str else backgroundColor
        self.color = colors[color] if type(color) == str else color
        self.t_w, self.t_h = estimate_text_size(text, self.size, self.weight)
        self.on_click = lambda x, y: None
        self.pressed = False

    def draw(self, frame):
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h), self.backgroundColor, -1)
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h),
                      [int(c * 0.7) for c in self.backgroundColor], 2)
        cv2.putText(
            frame,
            self.text,
            (self.x + self.w // 2 - int(self.t_w / 1.5), self.y + self.h // 2 + self.t_w // 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            self.size,
            self.color,
            self.weight
        )

    def onClick(self, callback):
        self.on_click = callback
