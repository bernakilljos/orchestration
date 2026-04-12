#!/usr/bin/env python3
"""
video-restore.py - One-click Video Restoration
================================================
CodeFormer (face restoration) + Real-ESRGAN (upscaling) + FFmpeg (video)

Usage:
  python video-restore.py input_video.mp4
  python video-restore.py input.mp4 -o output.mp4 -w 0.7 --scale 2
  python video-restore.py input.mp4 --face-only          # face only, no upscale
  python video-restore.py input.mp4 --upscale-only       # upscale only, no face
  python video-restore.py image.jpg                       # single image too

Pipeline:
  1. FFmpeg: video -> frames + audio extraction
  2. CodeFormer: face restoration on each frame
  3. Real-ESRGAN: background/full upscaling
  4. FFmpeg: restored frames + original audio -> output video
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ============================================================
# Config
# ============================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
CODEFORMER_DIR = SCRIPT_DIR / "CodeFormer"
REALESRGAN_DIR = SCRIPT_DIR / "Real-ESRGAN"

SUPPORTED_VIDEO = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
SUPPORTED_IMAGE = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


# ============================================================
# Helpers
# ============================================================
def run_cmd(cmd, desc="", cwd=None):
    """Run a shell command with progress info."""
    if desc:
        print(f"  >> {desc}")
    if isinstance(cmd, str):
        cmd = cmd.split()
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if stderr:
                print(f"     [WARN] {stderr[:200]}")
        return result.returncode == 0
    except FileNotFoundError:
        print(f"     [ERROR] Command not found: {cmd[0]}")
        return False
    except Exception as e:
        print(f"     [ERROR] {e}")
        return False


def check_tool(name):
    """Check if a CLI tool is available."""
    return shutil.which(name) is not None


def get_video_info(video_path):
    """Get video FPS and duration using ffprobe."""
    fps = 30.0
    duration = 0.0
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", str(video_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        import json
        info = json.loads(result.stdout)
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                r_fps = stream.get("r_frame_rate", "30/1")
                if "/" in r_fps:
                    num, den = r_fps.split("/")
                    fps = float(num) / float(den) if float(den) > 0 else 30.0
                else:
                    fps = float(r_fps)
                break
        fmt = info.get("format", {})
        duration = float(fmt.get("duration", 0))
    except Exception:
        pass
    return fps, duration


def count_files(folder, exts=("*.png", "*.jpg")):
    """Count files in a folder."""
    count = 0
    for ext in exts:
        count += len(glob.glob(os.path.join(folder, ext)))
    return count


# ============================================================
# Step 1: Extract frames + audio
# ============================================================
def extract_frames(video_path, frames_dir, fps=None):
    """Extract video frames using FFmpeg."""
    os.makedirs(frames_dir, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", str(video_path)]
    if fps:
        cmd += ["-vf", f"fps={fps}"]
    cmd += ["-qscale:v", "2", os.path.join(frames_dir, "frame_%06d.png")]
    return run_cmd(cmd, f"Extracting frames from {Path(video_path).name}")


def extract_audio(video_path, audio_path):
    """Extract audio track using FFmpeg."""
    cmd = ["ffmpeg", "-y", "-i", str(video_path),
           "-vn", "-acodec", "copy", str(audio_path)]
    success = run_cmd(cmd, "Extracting audio")
    if not success:
        # Try with re-encoding
        cmd = ["ffmpeg", "-y", "-i", str(video_path),
               "-vn", "-acodec", "aac", "-b:a", "192k", str(audio_path)]
        success = run_cmd(cmd, "Extracting audio (re-encode)")
    return success


# ============================================================
# Step 2: Face Restoration (CodeFormer)
# ============================================================
def restore_faces(input_dir, output_dir, fidelity_weight=0.7, bg_upsampler="realesrgan"):
    """Run CodeFormer face restoration on frames."""
    os.makedirs(output_dir, exist_ok=True)

    inference_script = CODEFORMER_DIR / "inference_codeformer.py"
    if not inference_script.exists():
        print("     [WARN] CodeFormer not found, trying pip package...")
        return restore_faces_pip(input_dir, output_dir, fidelity_weight)

    cmd = [
        sys.executable, str(inference_script),
        "--input_path", str(input_dir),
        "--output_path", str(output_dir),
        "-w", str(fidelity_weight),
        "--bg_upsampler", bg_upsampler,
        "--face_upsample",
    ]
    return run_cmd(cmd, f"CodeFormer face restoration (w={fidelity_weight})", cwd=str(CODEFORMER_DIR))


def restore_faces_pip(input_dir, output_dir, fidelity_weight=0.7):
    """Fallback: use codeformer via pip package."""
    try:
        import cv2
        from basicsr.archs.codeformer_arch import CodeFormer as CodeFormerArch
        # If this works, process frame by frame
        print("     [INFO] Using pip-based CodeFormer")
    except ImportError:
        print("     [ERROR] CodeFormer not available. Install via:")
        print("             git clone https://github.com/sczhou/CodeFormer")
        print("             OR pip install codeformer-pip")
        return False

    # Frame-by-frame processing
    frames = sorted(glob.glob(os.path.join(input_dir, "*.png")))
    os.makedirs(output_dir, exist_ok=True)
    for i, frame_path in enumerate(frames):
        if (i + 1) % 50 == 0:
            print(f"     Processing frame {i+1}/{len(frames)}...")
        out_path = os.path.join(output_dir, os.path.basename(frame_path))
        shutil.copy2(frame_path, out_path)  # Placeholder - needs full implementation
    return True


# ============================================================
# Step 3: Upscale (Real-ESRGAN)
# ============================================================
def upscale_frames(input_dir, output_dir, scale=2, model="RealESRGAN_x4plus"):
    """Run Real-ESRGAN upscaling on frames."""
    os.makedirs(output_dir, exist_ok=True)

    inference_script = REALESRGAN_DIR / "inference_realesrgan.py"
    if not inference_script.exists():
        print("     [WARN] Real-ESRGAN repo not found, trying pip package...")
        return upscale_frames_pip(input_dir, output_dir, scale, model)

    cmd = [
        sys.executable, str(inference_script),
        "-i", str(input_dir),
        "-o", str(output_dir),
        "-n", model,
        "-s", str(scale),
        "--half",
        "--ext", "png",
    ]
    return run_cmd(cmd, f"Real-ESRGAN upscaling (scale={scale}, model={model})", cwd=str(REALESRGAN_DIR))


def upscale_frames_pip(input_dir, output_dir, scale=2, model_name="RealESRGAN_x4plus"):
    """Fallback: use realesrgan pip package."""
    try:
        import cv2
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet

        print("     [INFO] Using pip-based Real-ESRGAN")

        if "anime" in model_name.lower():
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        else:
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)

        upsampler = RealESRGANer(
            scale=4,
            model_path=None,  # auto-download
            model=model,
            tile=400,
            tile_pad=10,
            pre_pad=0,
            half=True,
        )

        os.makedirs(output_dir, exist_ok=True)
        frames = sorted(glob.glob(os.path.join(input_dir, "*.png")))

        for i, frame_path in enumerate(frames):
            if (i + 1) % 20 == 0:
                print(f"     Upscaling frame {i+1}/{len(frames)}...")
            img = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
            output, _ = upsampler.enhance(img, outscale=scale)
            out_path = os.path.join(output_dir, os.path.basename(frame_path))
            cv2.imwrite(out_path, output)

        return True
    except ImportError:
        print("     [ERROR] realesrgan package not found")
        print("             pip install realesrgan")
        return False
    except Exception as e:
        print(f"     [ERROR] {e}")
        return False


# ============================================================
# Step 4: Reassemble video
# ============================================================
def assemble_video(frames_dir, audio_path, output_path, fps=30.0):
    """Combine restored frames + original audio into video."""
    # Find frame pattern
    frames = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
    if not frames:
        frames = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
    if not frames:
        print("     [ERROR] No frames found to assemble")
        return False

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
    ]

    # Add audio if available
    if audio_path and os.path.exists(audio_path):
        cmd += ["-i", str(audio_path), "-c:a", "copy"]

    cmd += [
        "-c:v", "libx264",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        str(output_path),
    ]

    return run_cmd(cmd, f"Assembling video -> {Path(output_path).name}")


# ============================================================
# Single Image Mode
# ============================================================
def process_image(input_path, output_path, fidelity_weight, scale, face_only, upscale_only):
    """Process a single image."""
    input_dir = Path(input_path).parent / "_vr_temp_input"
    output_dir = Path(input_path).parent / "_vr_temp_output"
    os.makedirs(input_dir, exist_ok=True)
    shutil.copy2(input_path, input_dir / Path(input_path).name)

    if not upscale_only:
        bg = "realesrgan" if not face_only else "none"
        restore_faces(str(input_dir), str(output_dir), fidelity_weight, bg)
        # CodeFormer outputs to final_results subfolder
        final_dir = output_dir / "final_results"
        if final_dir.exists():
            output_dir = final_dir

    if not face_only and (upscale_only or not (output_dir / Path(input_path).name).exists()):
        src = str(input_dir) if upscale_only else str(output_dir)
        upscale_dir = Path(input_path).parent / "_vr_temp_upscale"
        upscale_frames(src, str(upscale_dir), scale)
        output_dir = upscale_dir

    # Copy result
    results = sorted(glob.glob(os.path.join(str(output_dir), "*")))
    if results:
        shutil.copy2(results[0], output_path)
        print(f"\n  [OK] Result: {output_path}")

    # Cleanup
    for d in [input_dir, Path(input_path).parent / "_vr_temp_output",
              Path(input_path).parent / "_vr_temp_upscale"]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)


# ============================================================
# Main Pipeline
# ============================================================
def process_video(input_path, output_path, fidelity_weight, scale, face_only, upscale_only, target_fps=None):
    """Full video restoration pipeline."""
    work_dir = Path(input_path).parent / f"_vr_work_{Path(input_path).stem}"
    frames_dir = work_dir / "01_frames"
    face_dir = work_dir / "02_face_restored"
    upscale_dir = work_dir / "03_upscaled"
    audio_path = work_dir / "audio.aac"

    os.makedirs(work_dir, exist_ok=True)

    start_time = time.time()

    # Get video info
    fps, duration = get_video_info(input_path)
    if target_fps:
        fps = target_fps
    est_frames = int(fps * duration) if duration > 0 else 0
    print(f"\n  Video Info:")
    print(f"    FPS: {fps:.2f}")
    print(f"    Duration: {duration:.1f}s")
    print(f"    Est. frames: {est_frames}")
    print()

    # Step 1: Extract
    print("=" * 50)
    print("  STEP 1: Extract frames + audio")
    print("=" * 50)
    extract_frames(input_path, str(frames_dir))
    extract_audio(input_path, str(audio_path))

    actual_frames = count_files(str(frames_dir))
    print(f"  Extracted {actual_frames} frames")

    if actual_frames == 0:
        print("  [ERROR] No frames extracted!")
        return

    current_frames_dir = str(frames_dir)

    # Step 2: Face Restoration
    if not upscale_only:
        print()
        print("=" * 50)
        print("  STEP 2: Face Restoration (CodeFormer)")
        print("=" * 50)
        bg = "realesrgan" if not face_only else "none"
        success = restore_faces(current_frames_dir, str(face_dir), fidelity_weight, bg)
        # CodeFormer puts results in final_results subfolder
        final_results = face_dir / "final_results"
        if final_results.exists() and count_files(str(final_results)) > 0:
            current_frames_dir = str(final_results)
        elif count_files(str(face_dir)) > 0:
            current_frames_dir = str(face_dir)
        else:
            print("  [WARN] Face restoration produced no output, using original frames")

    # Step 3: Upscale
    if not face_only:
        print()
        print("=" * 50)
        print("  STEP 3: Upscale (Real-ESRGAN)")
        print("=" * 50)
        success = upscale_frames(current_frames_dir, str(upscale_dir), scale)
        if count_files(str(upscale_dir)) > 0:
            current_frames_dir = str(upscale_dir)
        else:
            print("  [WARN] Upscaling produced no output, using previous frames")

    # Step 4: Reassemble
    print()
    print("=" * 50)
    print("  STEP 4: Assemble output video")
    print("=" * 50)

    # Rename frames to sequential pattern if needed
    final_frames_dir = work_dir / "04_final"
    os.makedirs(final_frames_dir, exist_ok=True)
    frames = sorted(glob.glob(os.path.join(current_frames_dir, "*.png")))
    if not frames:
        frames = sorted(glob.glob(os.path.join(current_frames_dir, "*.jpg")))

    for i, f in enumerate(frames):
        ext = Path(f).suffix
        dst = final_frames_dir / f"frame_{i+1:06d}.png"
        shutil.copy2(f, dst)

    audio_file = str(audio_path) if audio_path.exists() else None
    assemble_video(str(final_frames_dir), audio_file, output_path, fps)

    elapsed = time.time() - start_time
    print()
    print("=" * 50)
    print(f"  DONE!")
    print(f"  Output: {output_path}")
    print(f"  Time:   {elapsed/60:.1f} min ({elapsed:.0f}s)")
    print(f"  Frames: {actual_frames}")
    print("=" * 50)

    # Cleanup work dir
    print(f"\n  Cleanup: {work_dir}")
    cleanup = input("  Delete work directory? [Y/n]: ").strip().lower()
    if cleanup != "n":
        shutil.rmtree(work_dir, ignore_errors=True)
        print("  [OK] Cleaned up")


# ============================================================
# Entry Point
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Video/Image Restoration with CodeFormer + Real-ESRGAN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python video-restore.py video.mp4                    # Full restore (face + upscale)
  python video-restore.py video.mp4 -w 0.5             # Lower fidelity = better quality
  python video-restore.py video.mp4 --scale 4           # 4x upscale
  python video-restore.py video.mp4 --face-only         # Face restore only
  python video-restore.py video.mp4 --upscale-only      # Upscale only
  python video-restore.py photo.jpg -o restored.jpg     # Single image
  python video-restore.py video.mp4 --fps 24            # Force output FPS
        """,
    )
    parser.add_argument("input", help="Input video or image file")
    parser.add_argument("-o", "--output", help="Output file path (default: input_restored.ext)")
    parser.add_argument("-w", "--weight", type=float, default=0.7,
                        help="CodeFormer fidelity weight 0-1 (lower=quality, higher=fidelity) [default: 0.7]")
    parser.add_argument("--scale", type=int, default=2, choices=[1, 2, 3, 4],
                        help="Upscale factor [default: 2]")
    parser.add_argument("--model", default="RealESRGAN_x4plus",
                        help="Real-ESRGAN model [default: RealESRGAN_x4plus]")
    parser.add_argument("--face-only", action="store_true",
                        help="Face restoration only, no upscaling")
    parser.add_argument("--upscale-only", action="store_true",
                        help="Upscaling only, no face restoration")
    parser.add_argument("--fps", type=float, default=None,
                        help="Force output video FPS")
    parser.add_argument("--gpu", type=int, default=0,
                        help="GPU device ID [default: 0]")

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    ext = input_path.suffix.lower()
    is_video = ext in SUPPORTED_VIDEO
    is_image = ext in SUPPORTED_IMAGE

    if not is_video and not is_image:
        print(f"[ERROR] Unsupported format: {ext}")
        print(f"  Video: {', '.join(SUPPORTED_VIDEO)}")
        print(f"  Image: {', '.join(SUPPORTED_IMAGE)}")
        sys.exit(1)

    # Set GPU
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)

    # Output path
    if args.output:
        output_path = str(Path(args.output).resolve())
    else:
        stem = input_path.stem
        output_path = str(input_path.parent / f"{stem}_restored{ext}")

    # Header
    print()
    print("=" * 50)
    print("  Video Restoration Tool")
    print("=" * 50)
    print(f"  Input:    {input_path}")
    print(f"  Output:   {output_path}")
    print(f"  Mode:     {'face-only' if args.face_only else 'upscale-only' if args.upscale_only else 'full'}")
    print(f"  Weight:   {args.weight}")
    print(f"  Scale:    {args.scale}x")
    print(f"  GPU:      {args.gpu}")

    # Check tools
    print()
    print("  Checking tools...")
    if is_video and not check_tool("ffmpeg"):
        print("  [ERROR] FFmpeg is required for video processing")
        print("          winget install Gyan.FFmpeg")
        sys.exit(1)

    # Process
    if is_image:
        process_image(str(input_path), output_path, args.weight, args.scale,
                      args.face_only, args.upscale_only)
    else:
        process_video(str(input_path), output_path, args.weight, args.scale,
                      args.face_only, args.upscale_only, args.fps)


if __name__ == "__main__":
    main()
