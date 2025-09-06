import json
import os
import subprocess
import tempfile
from logger_setup import log
from typing import Optional
from helpers import upload_to_github
from typing import Optional, Tuple

# ==============================================================================
#  STEP 1: HELPER FUNCTIONS (The code you already have)
# ==============================================================================


def get_video_properties(video_path: str) -> dict:
    """
    Returns a dictionary with video properties like width and height.
    """
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-select_streams",
        "v:0",
        video_path,
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        properties = json.loads(result.stdout)
        video_stream = properties["streams"][0]
        return {
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
        }
    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        IndexError,
        KeyError,
    ) as e:
        log.error(f"Failed to get video properties for {video_path}: {e}")
        return {}


def convert_video_for_instagram(input_path: str, output_path: str) -> bool:
    """
    Converts a video to be compliant with Instagram's feed post specifications (4:5 aspect ratio).
    """
    log.info(
        f"Converting '{input_path}' to Instagram-compliant format at '{output_path}'..."
    )
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "scale=1080:-2,crop=1080:1350",
        "-movflags",
        "+faststart",
        "-y",
        output_path,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        log.info("Successfully converted video.")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"FFmpeg conversion failed. FFmpeg stderr: {e.stderr}")
        return False


# ==============================================================================
#  STEP 2: THE NEW UTILITY FUNCTION
# ==============================================================================


def process_and_upload_video(
    local_path: str, platform: str = "instagram"
) -> Optional[str]:
    """
    Validates a local video, converts it if necessary, uploads it to GitHub,
    and returns the public URL. Handles temporary file cleanup.
    """
    if not os.path.exists(local_path):
        log.error(f"Input video file not found: {local_path}")
        return None

    path_to_upload = local_path
    needs_conversion = False

    # --- 1. Validate the video's properties ---
    props = get_video_properties(local_path)
    if not (props and props.get("width") and props.get("height")):
        log.error(f"Could not get video properties for {local_path}. Cannot proceed.")
        return None

    # --- 2. Decide if conversion is needed based on platform rules ---
    if platform in ["instagram", "threads"]:
        aspect_ratio = props["width"] / props["height"]
        if not (0.8 <= aspect_ratio <= 1.91):
            log.warning(
                f"Video for {platform} has invalid aspect ratio ({aspect_ratio:.2f}). Conversion required."
            )
            needs_conversion = True

    # --- 3. Convert (if needed) and upload ---
    if needs_conversion:
        # Create a temporary file that will be automatically deleted when we're done
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as temp_file:
            temp_output_path = temp_file.name

            # Convert the original video into the temporary file
            if not convert_video_for_instagram(local_path, temp_output_path):
                log.error(f"Failed to convert video {local_path}.")
                return None

            # Upload the newly converted temporary file
            log.info(
                f"Uploading converted video from temporary path: {temp_output_path}"
            )
            return upload_to_github(temp_output_path)
    else:
        # The original video is already compliant
        log.info(f"Video {local_path} is already compliant. Uploading original.")
        return upload_to_github(local_path)


def prepare_local_video(
    local_path: str,
) -> Tuple[str, Optional[tempfile._TemporaryFileWrapper]]:
    """
    Checks if a local video is compliant. If not, converts it to a temporary file.

    Returns a tuple containing:
    1. The path to the compliant video file (original or temporary).
    2. The temporary file object for cleanup (or None if no conversion was needed).
    """
    props = get_video_properties(local_path)
    if not (props and props.get("width") and props.get("height")):
        log.error(f"Could not get video properties for {local_path}.")
        return local_path, None  # Return original path and let the API decide

    aspect_ratio = props["width"] / props["height"]

    # If the video is already compliant, return the original path
    if 0.8 <= aspect_ratio <= 1.91:
        log.info(f"Video {local_path} is already compliant.")
        return local_path, None

    # If not compliant, create a temporary file and convert the video
    log.warning(f"Video {local_path} has non-compliant aspect ratio. Converting...")
    try:
        # Create a temp file that persists after being closed
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_file.close()  # Close the file so ffmpeg can write to it

        if convert_video_for_instagram(local_path, temp_file.name):
            return temp_file.name, temp_file
        else:
            # Conversion failed, return original and hope for the best
            os.remove(temp_file.name)  # Clean up failed temp file
            return local_path, None

    except Exception as e:
        log.error(f"Error during temporary file creation/conversion: {e}")
        return local_path, None
