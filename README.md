# VIDZ SCAN FAST

**VIDEO → SCAN → UNDERSTAND → MAP**

VIDZ SCAN FAST is a local video analysis machine.

Drop a video, scan it, and get a structured visual map:
- shot detection
- shot thumbnails
- duration and timing
- contact sheet
- machine-readable `.scan.json`
- lightweight motion / brightness / color metrics

## Philosophy

VIDZ TURN SHOT cuts.
VIDZ SCAN FAST understands and maps.

The generated `.scan.json` is designed to become a common memory format for the VIDZ / GOST OPERATOR toolchain.

## Requirements

- Python 3.10+
- ffmpeg installed and available in PATH

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 app.py
```

## Output

For `movie.mp4`, VIDZ SCAN FAST creates:

```
movie_SCAN/
├── movie.scan.json
├── contact_sheet.jpg
└── thumbnails/
    ├── shot_0001.jpg
    └── ...
```

## Current version

v0.1.0 — autonomous local scanner foundation.
