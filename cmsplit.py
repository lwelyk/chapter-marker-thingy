import os
import subprocess
import json
import argparse
from rich.console import Console
from rich.table import Table

FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"

console = Console()


def get_chapters(video_file):
    if not os.path.isfile(FFPROBE):
        console.print(f"[red]Error: ffprobe not found at {FFPROBE}[/red]")
        return None

    command = [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_chapters", video_file]
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()

    if process.returncode != 0:
        console.print(f"[red]Error: ffprobe failed on {video_file}[/red]")
        return None

    try:
        data = json.loads(stdout.decode())
    except json.JSONDecodeError:
        console.print("[red]Error: Could not parse ffprobe output[/red]")
        return None

    chapters = data.get("chapters", [])
    if not chapters:
        console.print("[yellow]No chapters found in video file[/yellow]")
        return None

    return chapters


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def split_chapters(video_file, output_prefix, start_number, dry_run=False):
    if not os.path.isfile(FFMPEG):
        console.print(f"[red]Error: ffmpeg not found at {FFMPEG}[/red]")
        return 1

    if not os.path.isfile(video_file):
        console.print(f"[red]Error: Video file not found: {video_file}[/red]")
        return 1

    chapters = get_chapters(video_file)
    if chapters is None:
        return 1

    _, ext = os.path.splitext(video_file)
    output_prefix = os.path.expanduser(output_prefix)

    # preview table
    table = Table(title="Chapters to Extract", show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Chapter", style="dim", justify="left")
    table.add_column("Start", style="green", justify="center")
    table.add_column("End", style="green", justify="center")
    table.add_column("Output File", style="yellow", justify="left")

    outputs = []
    for i, chapter in enumerate(chapters):
        ep_num = start_number + i
        output_file = f"{output_prefix}{ep_num:02d}{ext}"
        start_time = float(chapter["start_time"])
        end_time = float(chapter["end_time"])
        title = chapter.get("tags", {}).get("title", f"Chapter {i + 1}")
        outputs.append((start_time, end_time, output_file))
        table.add_row(
            str(ep_num),
            title,
            format_timestamp(start_time),
            format_timestamp(end_time),
            os.path.basename(output_file),
        )

    console.print(table)

    if dry_run:
        console.print("\n[bold yellow]Dry run — no files written.[/bold yellow]")
        return 0

    console.print()
    for i, (start_time, end_time, output_file) in enumerate(outputs):
        ep_num = start_number + i
        console.print(f"[bold cyan]Extracting episode {ep_num:02d}...[/bold cyan] → {os.path.basename(output_file)}")

        command = [
            FFMPEG,
            "-i", video_file,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",
            "-map_chapters", "-1",   # strip chapter metadata from output
            "-y",
            output_file,
        ]

        process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        _, error = process.communicate()

        if process.returncode == 0:
            console.print(f"  [green]✓ Done[/green]")
        else:
            console.print(f"  [red]✗ Failed[/red]")
            error_msg = error.decode()[-500:] if error else "Unknown error"
            console.print(f"  [dim]{error_msg}[/dim]")

    console.print(f"\n[bold green]Done! Extracted {len(outputs)} episode(s).[/bold green]")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Split a multi-episode video into one file per chapter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cmsplit.py -f input.mp4 -o "Show Name - s02e" --start-number 8
  python cmsplit.py -f input.mp4 -o "Show Name - s01e" --start-number 1 --dry-run
        """,
    )

    parser.add_argument("-f", "--file", required=True, help="Input video file")
    parser.add_argument(
        "-o", "--output",
        required=True,
        help='Output name prefix, e.g. "Show Name - s02e" (episode number and extension are appended)',
    )
    parser.add_argument(
        "--start-number",
        type=int,
        default=1,
        metavar="N",
        help="Episode number to start counting from (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the chapter list and output filenames without extracting anything",
    )

    args = parser.parse_args()

    return split_chapters(
        video_file=args.file,
        output_prefix=args.output,
        start_number=args.start_number,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    exit(main())