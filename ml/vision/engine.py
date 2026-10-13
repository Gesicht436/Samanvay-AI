"""PaddleOCR 3.x adapter. Pinned: paddleocr==3.7.0, paddlepaddle==3.3.1."""

import logging
import threading
from typing import Any, Optional

import numpy as np

from ml.vision.config import DEFAULT_CONFIG, OCRConfig
from ml.vision.exceptions import EngineCrashError

logger = logging.getLogger(__name__)

OCRItem = tuple[str, float, tuple[float, float, float, float]]


class PaddleOCREngine:
    _instance: Optional["PaddleOCREngine"] = None
    _lock = threading.Lock()

    def __new__(cls, config: OCRConfig = DEFAULT_CONFIG) -> "PaddleOCREngine":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init_engine(config)      # may raise; nothing is cached on failure
                cls._instance = inst
            return cls._instance

    def _init_engine(self, config: OCRConfig) -> None:
        self.config = config
        self.exec_lock = threading.Lock()
        try:
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR 3.x engine...")
            self._engine = PaddleOCR(
                lang="en",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
                enable_mkldnn=False,
            )
        except Exception as e:
            raise EngineCrashError(f"PaddleOCR init failed: {e}") from e

    @staticmethod
    def _parse(res: Any) -> list[OCRItem]:
        """Convert 3.x output to (text, score, bbox). Never drops low-confidence tokens."""
        if not res or res[0] is None:
            return []
        r = res[0]
        try:
            texts, scores, polys = r["rec_texts"], r["rec_scores"], r["rec_polys"]
        except (KeyError, TypeError) as e:
            raise EngineCrashError(f"Unrecognized OCR output shape: {type(r)}") from e
        if not (len(texts) == len(scores) == len(polys)):
            raise EngineCrashError("OCR output lists have mismatched lengths")
        out: list[OCRItem] = []
        for text, score, poly in zip(texts, scores, polys):
            xs = [float(p[0]) for p in poly]
            ys = [float(p[1]) for p in poly]
            out.append((str(text), float(score), (min(xs), min(ys), max(xs), max(ys))))
        return out

    def predict(self, image_np: np.ndarray) -> list[OCRItem]:
        """Thread-safe OCR on a BGR (or grayscale) numpy image."""
        if image_np.ndim == 2:
            image_np = np.stack([image_np] * 3, axis=-1)
        with self.exec_lock:
            try:
                return self._parse(self._engine.predict(image_np))
            except EngineCrashError:
                raise
            except Exception as e:
                raise EngineCrashError(f"PaddleOCR execution error: {e}") from e