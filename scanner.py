from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageDraw
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector


@dataclass
class Shot:
    index: int
    start: float
    end: float
    duration: float
    thumbnail: str
    brightness: float
    motion: float
    dominant_bgr: list[int]


def probe_video(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=width,height,r_frame_rate",
        "-of", "json", str(path)
    ]
    try:
        raw = subprocess.check_output(cmd, text=True)
        return json.loads(raw)
    except Exception:
        return {}


def detect_scenes(path: Path, threshold: float = 27.0):
    video = open_video(str(path))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=threshold))
    manager.detect_scenes(video)
    scenes = manager.get_scene_list()
    if not scenes:
        duration = video.duration
        scenes = [(video.base_timecode, duration)]
    return scenes


def frame_at(cap: cv2.VideoCapture, seconds: float):
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000.0)
    ok, frame = cap.read()
    return frame if ok else None


def metrics(frame, previous):
    if frame is None:
        return 0.0, 0.0, [0, 0, 0]

    small = cv2.resize(frame, (160, 90))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())

    mean_bgr = np.mean(small.reshape(-1, 3), axis=0)
    dominant = [int(x) for x in mean_bgr]

    motion = 0.0
    if previous is not None:
        prev = cv2.resize(previous, (160, 90))
        prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        motion = float(cv2.absdiff(gray, prev_gray).mean())

    return round(brightness, 2), round(motion, 2), dominant


def make_contact_sheet(images: list[Path], output: Path, cols: int = 5):
    if not images:
        return
    thumbs = []
    for p in images:
        im = Image.open(p).convert("RGB")
        im.thumbnail((320, 180))
        canvas = Image.new("RGB", (320, 205), "white")
        canvas.paste(im, ((320 - im.width)//2, 0))
        d = ImageDraw.Draw(canvas)
        d.text((8, 184), p.stem, fill="black")
        thumbs.append(canvas)

    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 320, rows * 205), "white")
    for i, im in enumerate(thumbs):
        x = (i % cols) * 320
        y = (i // cols) * 205
        sheet.paste(im, (x, y))
    sheet.save(output, quality=88)


def scan(video_path: str, progress=None, threshold: float = 27.0) -> Path:
    src = Path(video_path).expanduser().resolve()
    out = src.parent / f"{src.stem}_SCAN"
    thumbs_dir = out / "thumbnails"
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    if progress:
        progress(5, "DETECTING SHOTS")

    scenes = detect_scenes(src, threshold)
    cap = cv2.VideoCapture(str(src))
    shots = []
    thumb_paths = []
    prev_frame = None

    total = max(len(scenes), 1)
    for i, (start_tc, end_tc) in enumerate(scenes, start=1):
        start = start_tc.get_seconds()
        end = end_tc.get_seconds()
        middle = start + max((end - start) / 2, 0)
        frame = frame_at(cap, middle)

        thumb_name = f"shot_{i:04d}.jpg"
        thumb_path = thumbs_dir / thumb_name
        if frame is not None:
            cv2.imwrite(str(thumb_path), frame)
            thumb_paths.append(thumb_path)

        brightness, motion, dominant = metrics(frame, prev_frame)
        prev_frame = frame

        shots.append(Shot(
            index=i,
            start=round(start, 3),
            end=round(end, 3),
            duration=round(end - start, 3),
            thumbnail=f"thumbnails/{thumb_name}",
            brightness=brightness,
            motion=motion,
            dominant_bgr=dominant,
        ))

        if progress:
            pct = 10 + int((i / total) * 75)
            progress(pct, f"SCANNING SHOT {i}/{total}")

    cap.release()

    if progress:
        progress(90, "BUILDING MAP")

    contact = out / "contact_sheet.jpg"
    make_contact_sheet(thumb_paths, contact)

    payload = {
        "machine": "VIDZ SCAN FAST",
        "version": "0.1.0",
        "source": src.name,
        "source_path": str(src),
        "probe": probe_video(src),
        "shot_count": len(shots),
        "shots": [asdict(s) for s in shots],
        "outputs": {
            "contact_sheet": contact.name,
            "thumbnails": "thumbnails"
        }
    }

    json_path = out / f"{src.stem}.scan.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if progress:
        progress(100, "SCAN COMPLETE")
    return out
