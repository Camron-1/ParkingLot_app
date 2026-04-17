# 🚗 Smart Parking Detection (YOLOv8)

A computer vision–based smart parking system that detects vehicle occupancy in predefined parking spots using YOLOv8.  
Parking spots are manually defined as polygons, and the system determines whether each spot is **empty or full** in real time.

---

## ✨ Features

- 🎥 Real-time vehicle detection using **YOLOv8**
- 🅿️ Manual drawing of parking rows and spots
- 📐 Polygon-based occupancy detection
- 🟥 Automatic color change (green = empty, red = full)
- 🗂 Semi-transparent layout modal view
- ⚡ Optimized inference (YOLO runs periodically with cached detections)
- 🔗 Supports custom YouTube stream URL via command-line argument

---

## 🛠 Tech Stack

- Python
- OpenCV
- YOLOv8 (Ultralytics)
- NumPy
- FFmpeg (for stream decoding)

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/CAR-DETECTION.git
cd CAR-DETECTION
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure:
- `yolov8n.pt` is placed in the project root directory
- `ffmpeg` is installed and available in your system PATH

---

## ▶️ Running the Project

### Run with default YouTube stream

```bash
python main.py
```

### Run with a custom YouTube stream

```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

If no URL is provided, the system automatically falls back to the default stream defined in `main.py`.

---

## 🧠 How It Works

1. The admin defines parking rows and spots manually using polygon drawing.
2. YOLO detects vehicles in the video stream.
3. Detection runs every N frames for efficiency.
4. Cached bounding boxes are reused between inference cycles.
5. Each parking polygon is evaluated against detected vehicles.
6. Spots are marked:
   - 🟢 Green → Empty  
   - 🔴 Red → Occupied  

A layout modal allows visualization of rows and spots in sorted order.

---

## 🎯 Goal

This project explores the feasibility of a scalable, camera-based smart parking system capable of monitoring street parking and integrating with map-based applications.