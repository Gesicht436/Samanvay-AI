"""Print PaddleOCR 3.x output structure. Usage: python scripts\\discover_paddle.py [image_path]"""
import sys

import cv2
import numpy as np
import paddle
import paddleocr

print("python    ", sys.version.split()[0])
print("paddleocr ", paddleocr.__version__)
print("paddle    ", paddle.__version__)

if len(sys.argv) > 1:
    img = cv2.imread(sys.argv[1])
    if img is None:
        sys.exit(f"Could not read image: {sys.argv[1]}")
else:
    img = np.full((150, 500, 3), 255, dtype=np.uint8)
    cv2.putText(img, "TEST ASTM A105 0.18", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

ocr = paddleocr.PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
    enable_mkldnn=False,
)
res = ocr.predict(img)   # deliberately no try/except: I want the full traceback
r = res[0]
print("type  :", type(r))
print("keys  :", list(r.keys()))
print("texts :", r["rec_texts"][:10])
print("scores:", [round(float(s), 3) for s in r["rec_scores"][:10]])
print("poly0 :", r["rec_polys"][0] if len(r["rec_polys"]) else None)