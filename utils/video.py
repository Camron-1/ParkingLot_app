from yt_dlp import YoutubeDL
from typing import List, Tuple


# -----------------------------
# Stream utils
# -----------------------------
def pick_best_video_format(url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,

        # ✅ correct format
        "js_runtimes": {
            "node": {}
        },

        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    best = None

    for f in info.get("formats", []):
        # skip non-video formats
        if f.get("vcodec") in (None, "none"):
            continue

        # resolution
        h = f.get("height") or 0
        w = f.get("width") or 0

        # fallback if missing
        if not h or not w:
            res = f.get("resolution")
            if res and "x" in res:
                try:
                    w, h = map(int, res.split("x"))
                except:
                    pass

        # skip invalid or tiny formats
        if not w or not h or h < 240 or w < 320:
            continue

        protocol = f.get("protocol") or ""
        tbr = f.get("tbr") or 0  # bitrate

        # improved scoring
        score = (
            h,
            w,
            tbr,
            1 if protocol.startswith("m3u8") else 0
        )

        if best is None or score > best["score"]:
            best = {
                "fmt": f,
                "score": score,
                "w": w,
                "h": h
            }

    if best is None:
        raise RuntimeError("No valid video format found")

    f = best["fmt"]

    return (
        f["url"],
        best["w"],
        best["h"],
        f.get("format_id"),
        f.get("protocol")
    )

def read_exact(pipe, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = pipe.read(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def fit_to_screen(w, h, max_w, max_h):
    scale = min(max_w / w, max_h / h)
    scale = min(scale, 1.0)  # don't upscale

    new_w = int(w * scale)
    new_h = int(h * scale)

    return new_w, new_h