from typing import List, Tuple
from datetime import datetime, timezone

from ui.components import *
from utils.sort_layout import *

class System:
    buttons: List[Button] = []
    draw_stack: List[Line] = []
    rows: List[ParkingRow] = []
    current_row: Optional[ParkingRow] = None

    next_row_id: int = 1
    next_spot_id: int = 1

    state = {
        "row_edit": False,
        "adding_spot": False,
        "spot_previewing": False,
        "spot_line_count": 0,
        "layout_open": False,
    }

    # for auto-closing polygon on edge #4
    spot_first_point: Optional[Tuple[int, int]] = None

    # snapshot state before opening layout (so we restore it after closing)
    layout_prev = None

    # modal geometry cached (for X button placement + hit tests)
    modal_rect = None  # (mx, my, mw, mh)

    # close button (position updated dynamically)
    close_button: Optional[Button] = None

    # occupied_spots:int= 0
    # available_spots:int= 0



# -----------------------------
# Buttons: Add Row / Add Spot / End / Layout
# -----------------------------
add_row_btn_color  = (40, 120, 180)
add_spot_btn_color = (180, 120, 40)
end_btn_color      = (90, 90, 90)
layout_btn_color   = (70, 70, 70)

add_row_button  = Button(x=20,  y=40, w=140, h=50, text="add row",  backgroundColor=add_row_btn_color)
add_spot_button = Button(x=180, y=40, w=140, h=50, text="add spot", backgroundColor=add_spot_btn_color)
end_button      = Button(x=340, y=40, w=100, h=50, text="end",      backgroundColor=end_btn_color)
layout_button   = Button(x=460, y=40, w=140, h=50, text="layout",   backgroundColor=layout_btn_color)

def update_capacity():
    occupied_spots = 0
    available_spots = 0

    for row in System.rows:
        for spot in row.spots:
            if spot.full:
                occupied_spots += 1
            else:
                available_spots += 1

    capacity = occupied_spots + available_spots

    parking_status = create_parking_status(
        parking_lot_id="lot-a",
        name="Building 1 North Lot",
        capacity=capacity,
        occupied=occupied_spots
    )

    print(parking_status)

    return parking_status
    

def create_parking_status(
    parking_lot_id,
    name,
    capacity,
    occupied
):
    # Prevent occupied from going below 0 or above capacity
    occupied = max(0, min(occupied, capacity))

    # Calculate available spaces
    available = capacity - occupied

    # Calculate occupancy percentage
    if capacity > 0:
        occupancy_percentage = round((occupied / capacity) * 100, 2)
    else:
        occupancy_percentage = 0.0

    # Determine parking lot status
    if available == 0:
        status = "FULL"
    elif occupancy_percentage >= 80:
        status = "LIMITED"
    else:
        status = "AVAILABLE"

    # Create the final parking lot object
    parking_status = {
        "parkingLotId": parking_lot_id,
        "name": name,
        "capacity": capacity,
        "occupied": occupied,
        "available": available,
        "occupancyPercentage": occupancy_percentage,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    return parking_status
    
def refresh_buttons():
    """
    Normal mode buttons. (Layout mode will override buttons to just [X].)
    """
    System.buttons = [add_row_button, layout_button]
    if System.state["row_edit"]:
        System.buttons += [add_spot_button, end_button]


def reset_spot_mode():
    System.state["spot_previewing"] = False
    System.state["spot_line_count"] = 0
    System.spot_first_point = None


def onAddRow(x, y):
    if System.state["layout_open"]:
        return

    row = ParkingRow(id=System.next_row_id, spots=[])
    System.next_row_id += 1
    System.rows.append(row)

    System.current_row = row
    System.state["row_edit"] = True
    System.state["adding_spot"] = False
    reset_spot_mode()

    refresh_buttons()
    print(f"➕ Added row id={row.id}")


def onAddSpot(x, y):
    if System.state["layout_open"]:
        return

    if System.current_row is None:
        print("⚠️ No current row. Click 'add row' first.")
        return

    System.state["adding_spot"] = True
    reset_spot_mode()
    print(f"🅿️ Add spot mode ON (row id={System.current_row.id}). Draw 4 edges (click-click).")


def onEndRow(x, y):
    if System.state["layout_open"]:
        return

    if System.current_row is None:
        return

    # Rule:
    # - If row has >= 1 spot: end normally
    # - If row has 0 spots: delete it
    if len(System.current_row.spots) == 0:
        rid = System.current_row.id
        System.rows = [r for r in System.rows if r is not System.current_row]
        System.current_row = None
        System.state["row_edit"] = False
        System.state["adding_spot"] = False
        reset_spot_mode()
        refresh_buttons()
        print(f"🗑️ Deleted empty row id={rid}")
        return

    # normal end
    System.current_row = None
    System.state["row_edit"] = False
    System.state["adding_spot"] = False
    reset_spot_mode()
    refresh_buttons()
    print("✅ End row editing")

    print(f"Test") 

    update_capacity()

def open_layout():
    # Snapshot current interaction state so we can restore it after closing
    System.layout_prev = {
        "row_edit": System.state["row_edit"],
        "adding_spot": System.state["adding_spot"],
        "spot_previewing": System.state["spot_previewing"],
        "spot_line_count": System.state["spot_line_count"],
        "spot_first_point": System.spot_first_point,
        "current_row": System.current_row,
    }

    # Cancel any ability to draw while layout is open
    System.state["adding_spot"] = False
    reset_spot_mode()

    # Sort as requested when opening
    sort_layout_rows_and_spots()

    # Enable layout state and switch buttons to only X
    System.state["layout_open"] = True
    System.buttons = [System.close_button]  # close_button position updated each frame


def close_layout():
    # Restore previous state (bring everything "back to normal")
    prev = System.layout_prev or {}
    System.state["layout_open"] = False

    System.state["row_edit"] = bool(prev.get("row_edit", False))
    System.state["adding_spot"] = bool(prev.get("adding_spot", False))
    System.state["spot_previewing"] = bool(prev.get("spot_previewing", False))
    System.state["spot_line_count"] = int(prev.get("spot_line_count", 0))
    System.spot_first_point = prev.get("spot_first_point", None)
    System.current_row = prev.get("current_row", None)

    System.layout_prev = None
    refresh_buttons()


def onLayout(x, y):
    # If already open, do nothing (user must click X)
    if System.state["layout_open"]:
        return
    open_layout()
    print("🗂️ Layout opened (sorted rows/spots).")


def onCloseLayout(x, y):
    if not System.state["layout_open"]:
        return
    close_layout()
    print("🗂️ Layout closed.")


# -----------------------------
# Layout modal drawing (semi-transparent)
# -----------------------------
def draw_layout_modal(frame):
    H, W = frame.shape[:2]

    # modal size = 90% of window, centered
    mw = int(W * 0.90)
    mh = int(H * 0.90)
    mx = (W - mw) // 2
    my = (H - mh) // 2
    System.modal_rect = (mx, my, mw, mh)

    # update X button position (top-right inside modal)
    pad = 12
    System.close_button.x = mx + mw - pad - System.close_button.w
    System.close_button.y = my + pad

    # SEMI-TRANSPARENT overlay:
    overlay = frame.copy()
    modal_bg = (35, 35, 35)  # dark-ish grey
    border = (120, 120, 120)

    cv2.rectangle(overlay, (mx, my), (mx + mw, my + mh), modal_bg, -1)
    cv2.rectangle(overlay, (mx, my), (mx + mw, my + mh), border, 2)

    alpha = 0.72  # overlay opacity (0..1). higher = more opaque modal
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Title
    cv2.putText(frame, "LAYOUT (rows & spots)", (mx + 20, my + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, colors["white"], 2)

    # content area
    padding = 20
    x0 = mx + padding
    y0 = my + 60
    x1 = mx + mw - padding
    y1 = my + mh - padding

    row_gap = 22
    spot_gap = 10
    spot_w = 60
    spot_h = 30

    y_cursor = y0

    for row in System.rows:
        if y_cursor + spot_h + 40 > y1:
            cv2.putText(frame, "...", (x0, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, colors["white"], 2)
            break

        score = row_mean_of_spot_mean_y(row)
        cv2.putText(frame, f"Row {row.id}  (scoreY={score:.1f})", (x0, y_cursor),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors["white"], 2)

        y_cursor += 18

        x_cursor = x0
        line_base_y = y_cursor

        for spot in row.spots:
            if x_cursor + spot_w > x1:
                x_cursor = x0
                line_base_y += (spot_h + 8)

            if line_base_y + spot_h > y1:
                break

            outline_color = colors["red"] if spot.full else colors["green"]
            spot_color = (0, 0, 180) if spot.full else (0, 180, 0)
 
            cv2.rectangle(frame,
                        (x_cursor, line_base_y),
                        (x_cursor + spot_w, line_base_y + spot_h),
                        outline_color, -1)
            cv2.rectangle(frame,
                        (x_cursor, line_base_y),
                        (x_cursor + spot_w, line_base_y + spot_h),
                        spot_color, 2)

            cv2.putText(frame, f"S{spot.id}", (x_cursor + 6, line_base_y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, colors["black"], 2)

            x_cursor += (spot_w + spot_gap)

        y_cursor = line_base_y + spot_h + row_gap

    # Hint
    cv2.putText(frame, "Close with X (top-right)", (mx + 20, my + mh - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (210, 210, 210), 2)

    # Draw X button last (on top)
    System.close_button.draw(frame)

def sort_layout_rows_and_spots():
    """
    Spec:
    1) Sort rows DESC by mean( meanY(spot) )
    2) Sort spots ASC inside each row by meanX(spot)
    """
    for row in System.rows:
        row.spots.sort(key=spot_mean_x)  # ascending

    System.rows.sort(key=row_mean_of_spot_mean_y)  # descending


# -----------------------------
# Mouse handling
# -----------------------------
def point_in_btn(btn: Button, x: int, y: int) -> bool:
    return btn.x <= x <= (btn.x + btn.w) and btn.y <= y <= (btn.y + btn.h)


def brighten(c):
    return [min(255, int(v * 1.25)) for v in c]


def unbrighten(c):
    return [int(v / 1.25) for v in c]


def finalize_spot_if_ready():
    if System.current_row is None:
        return

    if System.state["spot_line_count"] >= 4:
        edges = System.draw_stack[-4:]
        spot = ParkingSpot(id=str(System.next_spot_id), lines=edges.copy())
        System.next_spot_id += 1
        System.current_row.spots.append(spot)

        # keep adding_spot True so you can continue drawing spots
        reset_spot_mode()
        print(f"✅ Spot added: row={System.current_row.id} spot={spot.id}")


add_row_button.onClick(onAddRow)
add_spot_button.onClick(onAddSpot)
end_button.onClick(onEndRow)
layout_button.onClick(onLayout)


# Close (X) button created once; position updated every frame based on modal rect
System.close_button = Button(x=0, y=0, w=44, h=40, text="X", backgroundColor=(60, 60, 60), color="white", size=0.8, weight=2)
System.close_button.onClick(onCloseLayout)

refresh_buttons()


# ===========================================================;
# ================== global mouse event =====================;
# ===========================================================;
def on_mouse(event, x, y, flags, param):
    on_top_of_button = False

    if event == cv2.EVENT_LBUTTONDOWN:
        # Button press styling
        for btn in System.buttons:
            if point_in_btn(btn, x, y):
                btn.backgroundColor = brighten(btn.backgroundColor)
                btn.pressed = True
                on_top_of_button = True

            if btn.pressed and not point_in_btn(btn, x, y):
                btn.pressed = False

        if not on_top_of_button:
            # If layout open, block everything (view-only)
            if System.state["layout_open"]:
                return

            # Spot drawing mode (click-click per edge)
            if System.state["adding_spot"] and System.current_row is not None:
                # start new edge
                if not System.state["spot_previewing"]:
                    System.state["spot_previewing"] = True

                    if System.state["spot_line_count"] == 0:
                        System.spot_first_point = (x, y)

                    System.draw_stack.append(Line((x, y), (x, y), 2, color="yellow"))
                    return

                # finalize current edge
                else:
                    # if finishing 4th edge, snap endpoint to first point
                    if System.state["spot_line_count"] == 3 and System.spot_first_point is not None:
                        end_x, end_y = System.spot_first_point
                    else:
                        end_x, end_y = x, y

                    System.draw_stack[-1].p2.x = end_x
                    System.draw_stack[-1].p2.y = end_y
                    System.state["spot_line_count"] += 1

                    if System.state["spot_line_count"] >= 4:
                        finalize_spot_if_ready()
                        return

                    # auto-start next edge from this endpoint
                    System.draw_stack.append(Line((end_x, end_y), (end_x, end_y), 2, color="yellow"))
                    return

    if event == cv2.EVENT_LBUTTONUP:
        # Button click dispatch
        for btn in System.buttons:
            if point_in_btn(btn, x, y) and btn.pressed:
                btn.backgroundColor = unbrighten(btn.backgroundColor)
                btn.pressed = False
                btn.on_click(x, y)
                return
            btn.pressed = False

    if event == cv2.EVENT_MOUSEMOVE:
        # Preview current edge endpoint while moving (disabled when layout open)
        if System.state["layout_open"]:
            return
        if System.state["spot_previewing"] and System.draw_stack:
            System.draw_stack[-1].p2.x = x
            System.draw_stack[-1].p2.y = y
