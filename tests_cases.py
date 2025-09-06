import sys
from destinations.threads import ThreadsDestination
from destinations.instagram import InstagramDestination

# --- 1. CONFIGURATION: Verify these paths are correct ---
# NOTE: These lists are now only used to populate the flat strings in test_cases below.
images_list = [
    "./test_image1.jpg",
    "./test_image2.jpg",
]
videos_list = [
    "./test_video1.mp4",
    "./test_video2.mp4",
]

# --- 2. DATA PREPARATION ---
# Define column names for clarity
TEXT_COLUMN_NAME = "Text"
IMAGE_URLS_COLUMN_NAME = "Image URLs"
VIDEO_URLS_COLUMN_NAME = "Video URLs"
HASHTAGS_COLUMN_NAME = "Hashtags"
HASHTAGS_IN_CAPTION_COLUMN_NAME = "Hashtags with TEXT"
THREADS_TEXT_ONLY_COLUMN_NAME = "Do Not Post Media on Threads"
LOCAL_IMAGE_PATH_COLUMN_NAME = "Local Image Path"
LOCAL_VIDEO_PATH_COLUMN_NAME = "Local Video Path"

# A list of dictionaries in the flat-string format.
test_cases = {
    # --- Instagram Test Cases ---
    "ig_text_with_image": {
        TEXT_COLUMN_NAME: "Instagram Test: A single image with text and hashtags in the caption.",
        LOCAL_IMAGE_PATH_COLUMN_NAME: images_list[0],
        HASHTAGS_COLUMN_NAME: "#instagram,#testing",
        HASHTAGS_IN_CAPTION_COLUMN_NAME: "TRUE",
    },
    "ig_text_with_video": {
        TEXT_COLUMN_NAME: "Instagram Test: A single video with text and hashtags in the first comment.",
        LOCAL_VIDEO_PATH_COLUMN_NAME: videos_list[0],
        HASHTAGS_COLUMN_NAME: "#video,#apitest",
        HASHTAGS_IN_CAPTION_COLUMN_NAME: "FALSE",
    },
    "ig_image_only": {
        TEXT_COLUMN_NAME: "",
        LOCAL_IMAGE_PATH_COLUMN_NAME: images_list[1],
    },
    "ig_two_images_carousel": {
        TEXT_COLUMN_NAME: "Instagram Test: A two-image carousel.",
        LOCAL_IMAGE_PATH_COLUMN_NAME: f"{images_list[0]},{images_list[1]}",
    },
    "ig_two_videos_carousel": {
        TEXT_COLUMN_NAME: "Instagram Test: A two-video carousel.",
        LOCAL_VIDEO_PATH_COLUMN_NAME: f"{videos_list[0]},{videos_list[1]}",
    },
    "ig_mixed_media_carousel": {
        TEXT_COLUMN_NAME: "Instagram Test: A mixed-media carousel (image and video).",
        LOCAL_IMAGE_PATH_COLUMN_NAME: images_list[1],
        LOCAL_VIDEO_PATH_COLUMN_NAME: videos_list[1],
    },
    # --- Threads Test Cases ---
    "threads_text_only": {
        TEXT_COLUMN_NAME: "Threads Test: This is a text-only post. #threads #textpost",
        THREADS_TEXT_ONLY_COLUMN_NAME: "TRUE",
    },
    "threads_text_with_image": {
        TEXT_COLUMN_NAME: "Threads Test: A single image with text. Hashtags will be posted as a reply.",
        LOCAL_IMAGE_PATH_COLUMN_NAME: images_list[0],
        HASHTAGS_COLUMN_NAME: "#threadstest,#image",
        HASHTAGS_IN_CAPTION_COLUMN_NAME: "FALSE",
    },
    "threads_text_with_video": {
        TEXT_COLUMN_NAME: "Threads Test: A single video with text and hashtags in the caption.",
        LOCAL_VIDEO_PATH_COLUMN_NAME: videos_list[0],
        HASHTAGS_COLUMN_NAME: "#videotest",
        HASHTAGS_IN_CAPTION_COLUMN_NAME: "TRUE",
    },
    "threads_two_images_carousel": {
        TEXT_COLUMN_NAME: "Threads Test: A carousel with two images.",
        LOCAL_IMAGE_PATH_COLUMN_NAME: f"{images_list[0]},{images_list[1]}",
    },
    "threads_two_videos_carousel": {
        TEXT_COLUMN_NAME: "Threads Test: A carousel with two videos.",
        LOCAL_VIDEO_PATH_COLUMN_NAME: f"{videos_list[0]},{videos_list[1]}",
    },
    "threads_mixed_media_carousel": {
        TEXT_COLUMN_NAME: "Threads Test: A mixed-media carousel (image and video).",
        LOCAL_IMAGE_PATH_COLUMN_NAME: images_list[1],
        LOCAL_VIDEO_PATH_COLUMN_NAME: videos_list[1],
    },
}


# --- 3. PARSER FUNCTION ---
def parse_content(flat_content: dict) -> dict:
    """
    Translates the flat-string content format into the structured format
    required by the destination classes.
    """
    structured_content = {}

    # Helper function to convert "TRUE" or "FALSE" strings to booleans
    def to_bool(value: str) -> bool:
        return value.upper() == "TRUE"

    # Process text
    structured_content[TEXT_COLUMN_NAME] = flat_content.get(TEXT_COLUMN_NAME, "")

    # Process boolean flags
    hashtags_in_caption = to_bool(
        flat_content.get(HASHTAGS_IN_CAPTION_COLUMN_NAME, "FALSE")
    )
    structured_content[HASHTAGS_IN_CAPTION_COLUMN_NAME] = hashtags_in_caption
    structured_content[THREADS_TEXT_ONLY_COLUMN_NAME] = to_bool(
        flat_content.get(THREADS_TEXT_ONLY_COLUMN_NAME, "FALSE")
    )

    # Process comma-separated paths into lists
    for key in [
        LOCAL_IMAGE_PATH_COLUMN_NAME,
        LOCAL_VIDEO_PATH_COLUMN_NAME,
        IMAGE_URLS_COLUMN_NAME,
        VIDEO_URLS_COLUMN_NAME,
    ]:
        path_str = flat_content.get(key, "")
        structured_content[key] = [
            path.strip() for path in path_str.split(",") if path.strip()
        ]

    # Process hashtags string into the list of dictionaries format
    hashtags_str = flat_content.get(HASHTAGS_COLUMN_NAME, "")
    hashtag_list = [ht.strip() for ht in hashtags_str.split(",") if ht.strip()]
    structured_content[HASHTAGS_COLUMN_NAME] = [
        {"hashtag": ht, "with_text": hashtags_in_caption} for ht in hashtag_list
    ]

    return structured_content


# --- 4. TEST IMPLEMENTATION ---
# Instantiate destinations once
inst_dest = InstagramDestination()
thr_dest = ThreadsDestination()


# --- Instagram Tests ---
def test_instagram_text_with_image():
    print("\n--- 📸 [Instagram] Testing: Text with Single Image ---")
    content = test_cases["ig_text_with_image"]
    inst_dest.post(content)


def test_instagram_text_with_video():
    print("\n--- 🎬 [Instagram] Testing: Text with Single Video ---")
    content = test_cases["ig_text_with_video"]
    inst_dest.post(content)


def test_instagram_image_only():
    print("\n--- 🖼️ [Instagram] Testing: Image Only ---")
    content = test_cases["ig_image_only"]
    inst_dest.post(content)


def test_instagram_two_images_carousel():
    print("\n--- 🖼️🖼️ [Instagram] Testing: Two-Image Carousel ---")
    content = test_cases["ig_two_images_carousel"]
    inst_dest.post(content)


def test_instagram_two_videos_carousel():
    print("\n--- 🖼️🎬 [Instagram] Testing: Two-Video Carousel ---")
    content = test_cases["ig_two_videos_carousel"]
    inst_dest.post(content)


def test_instagram_mixed_media_carousel():
    print("\n--- 🖼️🎬 [Instagram] Testing: Mixed-Media (Image + Video) Carousel ---")
    content = test_cases["ig_mixed_media_carousel"]
    inst_dest.post(content)


# --- Threads Tests ---
def test_threads_text_only():
    print("\n--- ✍️ [Threads] Testing: Text Only ---")
    content = test_cases["threads_text_only"]
    thr_dest.post(content)


def test_threads_text_with_image():
    print("\n--- ✍️📸 [Threads] Testing: Text with Single Image ---")
    content = test_cases["threads_text_with_image"]
    thr_dest.post(content)


def test_threads_text_with_video():
    print("\n--- ✍️🎬 [Threads] Testing: Text with Single Video ---")
    content = test_cases["threads_text_with_video"]
    thr_dest.post(content)


def test_threads_two_images_carousel():
    print("\n--- 📸📸 [Threads] Testing: Two-Image Carousel ---")
    content = test_cases["threads_two_images_carousel"]
    thr_dest.post(content)


def test_threads_two_videos_carousel():
    print("\n--- 🎬🎬 [Threads] Testing: Two-Video Carousel ---")
    content = test_cases["threads_two_videos_carousel"]
    thr_dest.post(content)


def test_threads_mixed_media_carousel():
    print("\n--- 🖼️🎬 [Threads] Testing: Mixed-Media (Image + Video) Carousel ---")
    content = test_cases["ig_mixed_media_carousel"]
    thr_dest.post(content)


# --- 5. TEST RUNNER ---
def run_all_tests():
    """
    Runs a series of tests sequentially, asking for user confirmation after each.
    """
    all_tests = [
        test_instagram_text_with_image,
        test_instagram_text_with_video,
        test_instagram_image_only,
        test_instagram_two_images_carousel,
        test_instagram_two_videos_carousel,  # Works when croped
        test_instagram_mixed_media_carousel,  # Works when croped
        test_threads_text_only,
        test_threads_text_with_image,
        test_threads_text_with_video,
        test_threads_two_images_carousel,
        test_threads_two_videos_carousel,
        test_threads_mixed_media_carousel,
    ]
    print("🚀 Starting automated posting tests...")
    for i, test_func in enumerate(all_tests, 1):
        try:
            test_func()
            print(f"✅ Test [{i}/{len(all_tests)}] API call executed.")
        except Exception as e:
            print(f"❌ ERROR during '{test_func.__name__}': {e}")
            print("Stopping tests due to error.")
            break

        while True:
            confirm = input("   succeeded? (y/n): ").lower().strip()
            if confirm in ["y", "n"]:
                break
            print("   Invalid input. Please enter 'y' or 'n'.")

        if confirm == "n":
            print("🛑 Tests stopped by user.")
            break
    else:
        print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    run_all_tests()
