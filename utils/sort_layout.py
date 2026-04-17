from typing import List, Tuple
from ui.components import *

# -----------------------------
# Sorting helpers (your spec)
# -----------------------------
def spot_vertices(spot: ParkingSpot) -> List[Tuple[int, int]]:
    """
    For a spot built by 4 sequential edges, the 4 vertices are edge.p1 points in order.
    """
    verts: List[Tuple[int, int]] = []
    if len(spot.edges) < 4:
        return verts
    for e in spot.edges[:4]:
        verts.append((e.p1.x, e.p1.y))
    return verts


def spot_mean_x(spot: ParkingSpot) -> float:
    verts = spot_vertices(spot)
    if len(verts) != 4:
        return float("inf")
    return sum(x for x, _ in verts) / 4.0


def spot_mean_y(spot: ParkingSpot) -> float:
    verts = spot_vertices(spot)
    if len(verts) != 4:
        return float("-inf")
    return sum(y for _, y in verts) / 4.0


def row_mean_of_spot_mean_y(row: ParkingRow) -> float:
    if not row.spots:
        return float("-inf")
    vals = [spot_mean_y(s) for s in row.spots]
    return sum(vals) / len(vals)




