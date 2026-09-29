"""Encode local, silent entrance reviews at native resolution and a close crop."""

import subprocess
from pathlib import Path
from typing import Iterable

from PIL import Image


def encode_previews(frames: Iterable[Image.Image], full: Path, close: Path, fps: int = 50) -> None:
    """Stream rendered RGB frames to H.264; the close crop is not upscaled."""
    crop = (480, 180, 1440, 720)  # 960x540: logo, scanner, password and action
    processes = []
    for destination, size in ((full, "1920x1080"), (close, "960x540")):
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", size,
            "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264",
            "-preset", "medium", "-crf", "13", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(destination),
        ]
        processes.append(subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE))
    try:
        for source in frames:
            if source.size != (1920, 1080):
                raise ValueError(f"expected 1920x1080 preview, got {source.size}")
            rgb = source.convert("RGB")
            processes[0].stdin.write(rgb.tobytes())
            processes[1].stdin.write(rgb.crop(crop).tobytes())
    finally:
        for process in processes:
            process.stdin.close()
    failures = []
    for process, path in zip(processes, (full, close)):
        error = process.stderr.read().decode(errors="replace")
        if process.wait() != 0:
            path.unlink(missing_ok=True)
            failures.append(f"{path}: {error}")
    if failures:
        raise RuntimeError("FFmpeg preview failed: " + "; ".join(failures))


def encode_video(frames: Iterable[Image.Image], path: Path, fps: int = 50) -> None:
    """Encode one full-HD review clip without adding an irrelevant close crop."""
    process = subprocess.Popen([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", "1920x1080",
        "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264",
        "-preset", "medium", "-crf", "13", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(path),
    ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for image in frames:
            if image.size != (1920, 1080):
                raise ValueError(f"expected 1920x1080 preview, got {image.size}")
            process.stdin.write(image.convert("RGB").tobytes())
        process.stdin.close()
        error = process.stderr.read().decode(errors="replace")
        if process.wait() != 0:
            raise RuntimeError(f"FFmpeg preview failed: {path}: {error}")
    except BaseException:
        if process.poll() is None:
            process.kill()
            process.wait()
        if not process.stdin.closed:
            process.stdin.close()
        path.unlink(missing_ok=True)
        raise
    finally:
        process.stderr.close()
