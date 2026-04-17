from typing import List, Tuple

# ======================= DETECTION CODE ====================
def polygon_from_spot(spot) -> List[Tuple[int, int]]:
    """
    Rebuild 4 vertices from the drawn edges.
    Assumption: edges are consecutive and represent the polygon border.
    Using p1 of each edge gives the vertex chain.
    """
    if not hasattr(spot, "edges") or len(spot.edges) < 4:
        return []
    return [(e.p1.x, e.p1.y) for e in spot.edges[:4]]


def polygon_area(poly: List[Tuple[int, int]]) -> float:
    """Shoelace formula. Returns absolute area."""
    if len(poly) < 3:
        return 0.0
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def point_in_poly(px: float, py: float, poly: List[Tuple[int, int]]) -> bool:
    """
    Ray casting algorithm.
    Works for convex/concave polygons (your spots are usually convex).
    """
    inside = False
    n = len(poly)
    if n < 3:
        return False

    x1, y1 = poly[0]
    for i in range(1, n + 1):
        x2, y2 = poly[i % n]
        # check if point is between y1 and y2
        if ((y1 > py) != (y2 > py)):
            # compute x intersection of edge with ray at py
            x_int = (x2 - x1) * (py - y1) / (y2 - y1 + 1e-9) + x1
            if px < x_int:
                inside = not inside
        x1, y1 = x2, y2
    return inside


def clip_polygon_with_rect(poly: List[Tuple[int, int]], rect: Tuple[int, int, int, int]) -> List[Tuple[float, float]]:
    """
    Sutherland–Hodgman polygon clipping for axis-aligned rectangle.
    rect = (rx1, ry1, rx2, ry2)
    Returns a polygon (list of points) representing intersection poly ∩ rect.
    """
    rx1, ry1, rx2, ry2 = rect

    def clip_edge(points, inside_fn, intersect_fn):
        if not points:
            return []
        out = []
        prev = points[-1]
        prev_in = inside_fn(prev)
        for curr in points:
            curr_in = inside_fn(curr)
            if curr_in:
                if not prev_in:
                    out.append(intersect_fn(prev, curr))
                out.append(curr)
            elif prev_in:
                out.append(intersect_fn(prev, curr))
            prev, prev_in = curr, curr_in
        return out

    def inside_left(p):   return p[0] >= rx1
    def inside_right(p):  return p[0] <= rx2
    def inside_top(p):    return p[1] >= ry1
    def inside_bottom(p): return p[1] <= ry2

    def intersect_vertical(p1, p2, x):
        x1, y1 = p1; x2, y2 = p2
        t = (x - x1) / (x2 - x1 + 1e-9)
        y = y1 + t * (y2 - y1)
        return (x, y)

    def intersect_horizontal(p1, p2, y):
        x1, y1 = p1; x2, y2 = p2
        t = (y - y1) / (y2 - y1 + 1e-9)
        x = x1 + t * (x2 - x1)
        return (x, y)

    out_poly: List[Tuple[float, float]] = [(float(x), float(y)) for x, y in poly]

    out_poly = clip_edge(out_poly, inside_left,   lambda a, b: intersect_vertical(a, b, rx1))
    out_poly = clip_edge(out_poly, inside_right,  lambda a, b: intersect_vertical(a, b, rx2))
    out_poly = clip_edge(out_poly, inside_top,    lambda a, b: intersect_horizontal(a, b, ry1))
    out_poly = clip_edge(out_poly, inside_bottom, lambda a, b: intersect_horizontal(a, b, ry2))

    return out_poly


def polygon_area_float(poly: List[Tuple[float, float]]) -> float:
    if len(poly) < 3:
        return 0.0
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def is_full(
    box: Tuple[int, int, int, int],
    parking_poly: List[Tuple[int, int]],
    *,
    center_required: bool = True,
    overlap_threshold: float = 0.2
) -> bool:
    """
    Returns True if the spot is 'full' given a car bounding box and a parking polygon.

    Strategy:
    1) Check if car box center is inside polygon (fast & stable).
    2) OR check overlap ratio = area(poly ∩ box) / area(poly) >= overlap_threshold.

    You can tune overlap_threshold depending on your camera angle.
    """
    if len(parking_poly) < 3:
        return False

    x1, y1, x2, y2 = box
    if x2 <= x1 or y2 <= y1:
        return False

    # 1) Center-in-polygon
    cx = (x1 + x2) * 0.5
    cy = (y1 + y2) * 0.5
    center_in = point_in_poly(cx, cy, parking_poly)

    if center_required and center_in:
        return True

    # 2) Overlap ratio: (poly ∩ box) / poly_area
    p_area = polygon_area(parking_poly)
    if p_area <= 1e-6:
        return False

    inter_poly = clip_polygon_with_rect(parking_poly, (x1, y1, x2, y2))
    inter_area = polygon_area_float(inter_poly)
    ratio = inter_area / p_area

    return ratio >= overlap_threshold or (not center_required and center_in)
# ======================= DETECTION CODE ====================