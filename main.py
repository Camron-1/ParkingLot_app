
import argparse
import subprocess

import cv2
import numpy as np

from typing import Union, Tuple, List, Optional

from ultralytics import YOLO

from system import *

from lib.polygon import *
from ui.components import *
from utils.sort_layout import *
from utils.video import *

import tkinter as tk

root = tk.Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.destroy()



# -----------------------------
# Main (stream + render)
# -----------------------------
parser = argparse.ArgumentParser(description="Smart Parking Detection Stream")
parser.add_argument("--url", type=str, help="YouTube stream URL")
args = parser.parse_args()

DEFAULT_YOUTUBE_URL = "https://www.youtube.com/watch?v=4a-3iEM7bHk"
YOUTUBE_URL = args.url if args.url else DEFAULT_YOUTUBE_URL

stream_url, w, h, fmt_id, proto = pick_best_video_format(YOUTUBE_URL)

w, h = fit_to_screen(w, h, screen_w, screen_h)

w -= w % 2
h -= h % 2

print("Chosen format:", fmt_id, proto, f"{w}x{h}")

if not w or not h:
    raise RuntimeError("Could not get width/height from format metadata.")

ffmpeg_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "error",

    "-fflags", "nobuffer",
    "-flags", "low_delay",
    "-strict", "experimental",
    "-rtbufsize", "100M",

    "-reconnect", "1",
    "-reconnect_streamed", "1",
    "-reconnect_delay_max", "5",

    "-i", stream_url,

    "-an",
    "-vsync", "0",

    "-vf", f"scale={w}:{h}",

    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "pipe:1",
]

proc = subprocess.Popen(
    ffmpeg_cmd,
    stdout=subprocess.PIPE,
    bufsize=10**8
)

WINDOW_NAME = "YouTube Live (HQ)"
frame_size = w * h * 3
cv2.namedWindow(WINDOW_NAME)
cv2.setMouseCallback(WINDOW_NAME, on_mouse)

# YOLO setup
model = YOLO("yolov8n.pt") # deep learning detection of objects
CAR_CLASS_ID = 2
CONF_THRES = 0.2

#===============================
# YOLO caching: run inference only once every 60 frames,
# reuse last detections for the frames in-between.
YOLO_EVERY = 20
last_car_boxes = []  # list of (x1,y1,x2,y2)
i = 0
#===============================

while True:
    raw = read_exact(proc.stdout, frame_size)
    if raw is None:
        break

    frame = np.frombuffer(raw, np.uint8).reshape((h, w, 3)).copy()

    #===============================
    # YOLO inference throttling + cache reuse
    if i % YOLO_EVERY == 0:
        # Run YOLO only every 60 frames
        last_car_boxes = []
        results = model.predict(frame, conf=CONF_THRES, verbose=False)[0]
        if results.boxes is not None and len(results.boxes) > 0:
            for b in results.boxes:
                if int(b.cls.item()) != CAR_CLASS_ID:
                    continue
                x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                last_car_boxes.append((x1, y1, x2, y2))

    # Draw cached boxes on every frame (including inference frames)
    for (x1, y1, x2, y2) in last_car_boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), colors["blue"], 2)
    #===============================


    # ======================= DETECTION CODE ====================
    # Run occupancy detection one frame after YOLO inference frame
    # (i % YOLO_EVERY == 1), using cached last_car_boxes
    if i % YOLO_EVERY == 1:
        for row in System.rows:
            for spot in row.spots:
                poly = polygon_from_spot(spot)
                spot_is_full = False

                # check this spot against all detected car boxes
                for (x1, y1, x2, y2) in last_car_boxes:
                    if is_full((x1, y1, x2, y2), poly, center_required=True, overlap_threshold=0.2):
                        spot_is_full = True
                        break

                spot.full = spot_is_full
    # ======================= DETECTION CODE ====================

    # Draw existing rows/spots on main view (optional)
    for row in System.rows:
        row.draw(frame, thickness=2, color="cyan")

    # Draw lines (includes temporary edges)
    for shape in System.draw_stack:
        shape.draw(frame)

    # Draw UI buttons (normal mode) OR just X button (layout mode)
    for btn in System.buttons:
        btn.draw(frame)

    # HUD (kept simple)
    cv2.putText(frame, f"Rows: {len(System.rows)}", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors["white"], 2)

    if System.current_row is not None:
        cv2.putText(frame, f"Editing Row: {System.current_row.id} | Spots: {len(System.current_row.spots)}",
                    (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors["white"], 2)

    if System.state["adding_spot"] and not System.state["layout_open"]:
        cv2.putText(frame, f"Add-Spot Mode: ON | Edge {System.state['spot_line_count'] + 1}/4",
                    (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors["yellow"], 2)

    # Layout modal overlay (semi-transparent) + X button
    if System.state["layout_open"]:
        # while layout is open, override buttons to only [X]
        System.buttons = [System.close_button]
        draw_layout_modal(frame)

    else:
        # ensure normal buttons are in place when layout is closed
        refresh_buttons()

    #===============================
    i += 1
    #===============================

    cv2.imshow(WINDOW_NAME, frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

proc.terminate()
cv2.destroyAllWindows()