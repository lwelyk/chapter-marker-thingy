# Chapter Marker Thingy

A pair of tools for working with chapter markers in videos.

- **`cmthingy.py`** — Detects commercial break points in old TV recordings and adds chapter markers
- **`cmsplit.py`** — Splits a multi-episode video into one file per chapter

## Requirements

- Python 3.x
- ffmpeg / ffprobe (configured at the top of each script)
- `pip install rich`

---

## cmthingy.py — Commercial Break Detector

Automatically finds good places to put chapter markers in videos by detecting black frames, silence, and scene changes.

### What it does

It uses a two-pass approach:

1. First it looks for black frames (the natural commercial breaks)
2. Then it finds in any big gaps with scene changes that also have silence nearby

### Usage

Process a single video:
```bash
python cmthingy.py -f video.mp4
```

Process a whole directory:
```bash
python cmthingy.py -d /path/to/videos
```

Write chapter markers to the videos:
```bash
python cmthingy.py -f video.mp4 --write-chapters
```

Overwrite the original files instead of creating `.chapters` files:
```bash
python cmthingy.py -f video.mp4 --write-chapters --overwrite
```

Adjust the maximum gap before it inserts a scene-based break (default is 12 minutes):
```bash
python cmthingy.py -f video.mp4 --max-gap 15
```

Limit the number of breaks per hour of video (useful when too many breaks are detected):
```bash
python cmthingy.py -f video.mp4 --max-breaks-per-hour 5
```

### How it works

The script runs ffmpeg to detect:
- **Black frames**: Usually indicate commercial breaks
- **Silence**: Helps confirm break points
- **Scene changes**: Used to fill large gaps when there aren't enough black frames

It scores each potential break point based on:
- Distance from ideal position (8 minute intervals)
- Presence of black frames (+10 points)
- Presence and duration of silence (+5-9 points)
- Scene changes (baseline)

Only scene changes with a score of 3+ are used (ensures silence is nearby).

When `--max-breaks-per-hour` is specified, it limits the total breaks based on video duration (e.g., a 45-minute video with `--max-breaks-per-hour 5` allows up to 4 breaks). It picks the highest-scoring breaks while keeping them at least 2 minutes apart to avoid clustering.

### Output

Shows a nice table with:
- Timestamp
- Type (black frame or scene change)
- Confidence level
- Whether silence was detected nearby

```
                         Commercial Break Points
┏━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ # ┃ Timestamp ┃ Time (seconds) ┃     Type     ┃ Confidence ┃ Silence? ┃
┡━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 1 │   12:52   │        772.92s │ Scene Change │    HIGH    │    ✓     │
│ 2 │   27:22   │       1642.52s │ Black Frame  │    HIGH    │    ✓     │
│ 3 │   50:45   │       3045.62s │ Scene Change │    HIGH    │    ✓     │
│ 4 │   72:41   │       4361.65s │ Black Frame  │    HIGH    │    ✓     │
│ 5 │   74:08   │       4448.69s │ Black Frame  │    HIGH    │    ✓     │
│ 6 │  105:48   │       6348.71s │ Scene Change │    HIGH    │    ✓     │
│ 7 │  140:20   │       8420.90s │ Black Frame  │    HIGH    │          │
└───┴───────────┴────────────────┴──────────────┴────────────┴──────────┘
```

If you use `--write-chapters`:
- Creates chapter markers in FFMETADATA format and adds them to the video file
- By default, creates a new file with `.chapters` added to the name (e.g., `video.chapters.mp4`)
- With `--overwrite`, replaces the original file (writes to a temp file first, then swaps it)
- Original quality is preserved — it's just copying streams and adding metadata

### Notes

- Update the `FFMPEG` path at the top of the script to match your system
- Black frames at the very start/end of videos are ignored (not real commercial breaks)
- Use `--overwrite` carefully — it replaces your original files (though it does use a temp file for safety)

---

## cmsplit.py — Episode Splitter

Splits a video file with chapter markers into one file per chapter, named sequentially. Useful when you have multiple episodes of a show joined into a single file.

### Usage

```bash
python cmsplit.py -f input_video.mp4 -o "Show Name - s02e" --start-number 8
```

This reads the chapter markers from `input_video.mp4` and outputs one file per chapter:

```
Show Name - s02e08.mp4
Show Name - s02e09.mp4
Show Name - s02e10.mp4
...
```

Preview what would be extracted without writing any files:
```bash
python cmsplit.py -f input_video.mp4 -o "Show Name - s02e" --start-number 8 --dry-run
```

### Arguments

| Argument | Description |
| --- | --- |
| `-f`, `--file` | Input video file |
| `-o`, `--output` | Output name prefix (episode number and extension are appended) |
| `--start-number N` | Episode number to start counting from (default: 1) |
| `--dry-run` | Preview chapter list and filenames without extracting |

### Notes

- Episode numbers are zero-padded to two digits (`08`, `09`, `10`, ...)
- The output file extension matches the input file
- Output paths support `~` expansion
- Chapter metadata is stripped from the individual output files
- Update the `FFMPEG` and `FFPROBE` paths at the top of the script to match your system

### Typical workflow

1. Use `cmthingy.py --write-chapters` to detect and embed chapter markers
2. Use `cmsplit.py` to split on those markers into individual episode files