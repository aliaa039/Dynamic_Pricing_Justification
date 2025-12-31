"""
Configuration constants for Re-Commerce AI Inspector
"""

# ---------------- Product Inspection Configuration ----------------
PRODUCT_INSPECTION_VIEWS = {
    "Laptop": {
        "num_views": 6,
        "views": [
            "Screen on (front, open)",
            "Keyboard & trackpad",
            "Top lid (closed)",
            "Left side ports",
            "Right side ports",
            "Bottom panel"
        ]
    },
    "Mobile": {
        "num_views": 6,
        "views": [
            "Front screen",
            "Back panel",
            "Left side (buttons)",
            "Right side (buttons)",
            "Bottom edge (charging port)",
            "Camera close-up"
        ]
    }
}

# ---------------- Resolution and Margin Requirements ----------------
CONFIG = {
    "Laptop": {
        "min_width": 800,
        "min_height": 600,
        "required_margin": 0.6
    },
    "Mobile": {
        "min_width": 400,
        "min_height": 300,
        "required_margin": 0.3
    }
}

VIEW_REQUIRED_MARGINS = {
    # Laptop views - relaxed for regular users
    "Screen on (front, open)": 0.35,
    "Keyboard & trackpad": 0.10,
    "Top lid (closed)": 0.15,
    "Bottom panel": 0.30,

    # Side views → nearly zero margin (accept everything)
    "Left side ports": 0.005,
    "Right side ports": 0.005,

    # Mobile - relaxed for regular photography
    "Front screen": 0.25,
    "Back panel": 0.18,
    "Left side (buttons)": 0.05,
    "Right side (buttons)": 0.05,
    "Bottom edge (charging port)": 0.15,
    "Camera close-up": 0.20,
}

# ---------------- CLIP Thresholds ----------------
CLIP_TOP1_TOP2_MARGIN = 1.5
CLIP_EXPECTED_VS_UNRELATED = 1.0
CLIP_MAX_UNRELATED_ALLOWED = 0.45

# ---------------- CLIP Product Labels ----------------
CLIP_PRODUCT_LABELS = [
    "a photo of a laptop computer",
    "a photo of a smartphone",
    "a photo of an unrelated object, artwork, pattern, or scenery"
]

CLIP_PRODUCT_CLASS_TO_NAME = {0: "Laptop", 1: "Mobile", 2: "Unrelated"}
CATEGORY_TO_CLIP_CLASS = {"Laptop": 0, "Mobile": 1}

# ---------------- CLIP View Labels ----------------
VIEW_CLIP_LABELS = {
    "Screen on (front, open)": [
        "a clear photo showing the full screen of an open laptop",
        "a photo of just the laptop keyboard, screen not visible",
        "a close-up portrait of a single corner or hinge of a laptop",
        "a photo of an unrelated object, blurry scene, or extremely cropped image"
    ],
    "Keyboard & trackpad": [
        "a photo showing a laptop keyboard",
        "a photo of an unrelated object or scenery"
    ],
    "Top lid (closed)": [
        "a photo of the smooth outer top lid of a closed laptop with brand logo or stickers",
        "a photo of the bottom base panel of a laptop with vents screws and rubber feet",
        "a photo of an open laptop showing keyboard or screen",
        "a photo of an unrelated object"
    ],
    "Left side ports": [
        "a photo of the left side edge of a laptop",
        "a photo of an unrelated object or scenery"
    ],
    "Right side ports": [
        "a photo of the right side edge of a laptop",
        "a photo of an unrelated object or scenery"
    ],
     "Bottom panel": [
        "a photo of the large flat bottom base panel of a laptop with screws vents and rubber feet",
        "a photo of the smooth top lid of a closed laptop with brand logo",
        "a photo of the narrow side edge of a laptop",
        "a photo of an unrelated object"
    ],
    "Front screen": [
        "a handheld mobile photo of the front screen display of a smartphone with bezels and notch",
        "a photo of the back panel of a phone with camera lenses",
        "a photo of an unrelated object"
    ],
    "Back panel": [
        "a wide photo of the complete full back panel of a smartphone showing the entire uncropped rear surface from top to bottom",
        "a cropped close-up photo showing only part of the phone or just the camera module",
        "a photo of the front screen of a smartphone",
        "a photo of an unrelated object"
    ],
     "Left side (buttons)": [
        "a photo of the side edge of a smartphone with volume or power buttons",
        "a photo of the bottom edge with charging port and speaker holes",
        "a photo of an unrelated object"
    ],
    "Right side (buttons)": [
        "a photo of the side edge of a smartphone with volume or power buttons",
        "a photo of the bottom edge with charging port and speaker holes",
        "a photo of an unrelated object"
    ],
    "Bottom edge (charging port)": [
        "a photo of the bottom edge of a smartphone showing USB charging port and speaker holes",
        "a photo of the side edge of a smartphone showing volume or power buttons",
        "a photo of an unrelated object"
    ],
    "Camera close-up": [
        "a close-up handheld photo of the rear camera lens and sensors of a smartphone",
        "a photo of an unrelated object"
    ]
}
