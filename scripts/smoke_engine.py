"""Smoke test script to verify PaddleOCREngine predict execution on a real image file."""

import sys
from pathlib import Path
import cv2
import numpy as np

from ml.vision.engine import PaddleOCREngine


def main() -> None:
    if len(sys.argv) > 1:
        img_path = Path(sys.argv[1])
    else:
        found_images = list(Path("datasets").glob("**/*.png")) + list(Path("datasets").glob("**/*.jpg"))
        if found_images:
            img_path = found_images[0]
        else:
            img_path = None

    if img_path and img_path.exists():
        print(f"Loading image from: {img_path}")
        image_np = cv2.imread(str(img_path))
    else:
        print("No image file path provided or found in datasets/. Creating synthetic test image...")
        image_np = np.full((200, 500, 3), 255, dtype=np.uint8)
        cv2.putText(
            image_np,
            "HEAT NO: H-99482 GRADE: ASTM A105",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2,
        )

    print("Initializing PaddleOCREngine singleton...")
    engine = PaddleOCREngine()

    print("Executing predict() on image payload...")
    results = engine.predict(image_np)

    print(f"\n--- SMOKE TEST RESULTS ---")
    print(f"Extracted Blocks Count: {len(results)}")
    for idx, (text, score, bbox) in enumerate(results[:5]):
        print(f"[{idx + 1}] Text: '{text}' | Score: {score:.4f} | BBox: {bbox}")


if __name__ == "__main__":
    main()
