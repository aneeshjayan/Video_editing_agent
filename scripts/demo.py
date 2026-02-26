"""CLI demo script for the video editing agent.

Usage:
    python scripts/demo.py --video path/to/video.mp4 --instruction "trim first 10 seconds"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.flow import VideoEditFlow


def main():
    parser = argparse.ArgumentParser(
        description="AI Video Editor - CLI Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python scripts/demo.py --video sample.mp4 --instruction "trim first 10 seconds"\n'
            '  python scripts/demo.py --video sample.mp4 --instruction "add fade transitions"\n'
            '  python scripts/demo.py --video sample.mp4 --instruction "create 30s highlight reel"\n'
        ),
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Path to the input video file",
    )
    parser.add_argument(
        "--instruction",
        required=True,
        help="Natural language editing instruction",
    )

    args = parser.parse_args()

    # Validate input
    if not Path(args.video).exists():
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)

    # Run pipeline
    print("=" * 60)
    print("AI Video Editor - CLI Demo")
    print("=" * 60)
    print(f"Video: {args.video}")
    print(f"Instruction: {args.instruction}")
    print("=" * 60)

    def on_progress(state):
        print(f"  [{state.progress_percent:3d}%] {state.current_stage.value}")
        if state.logs:
            latest = state.logs[-1]
            print(f"        {latest}")

    flow = VideoEditFlow()
    result = flow.run(
        video_path=args.video,
        user_instruction=args.instruction,
        progress_callback=on_progress,
    )

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"Status: {result.status}")
    print(f"Job ID: {result.job_id}")

    if result.status == "completed":
        print(f"Output: {result.output_path}")
        print("\nAgent Output:")
        print(result.crew_output[:1000])
    else:
        print(f"Error: {result.error}")

    print("\nFull Log:")
    for entry in result.logs:
        print(f"  {entry}")


if __name__ == "__main__":
    main()
