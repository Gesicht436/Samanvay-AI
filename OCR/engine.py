"""PaddleOCR 2.x/3.x adapter with EasyOCR fallback."""

import os
from importlib import import_module
from statistics import median
from typing import Any


def _box_vertical_bounds(block: dict[str, Any]) -> tuple[float, float]:
    box = block.get("box")
    if isinstance(box, (list, tuple)):
        if len(box) == 4 and all(isinstance(value, (int, float)) for value in box):
            return float(box[1]), float(box[3])
        points = [
            point
            for point in box
            if isinstance(point, (list, tuple))
            and len(point) >= 2
            and isinstance(point[1], (int, float))
        ]
        if points:
            ys = [float(point[1]) for point in points]
            return min(ys), max(ys)

    y = float(block.get("y", 0))
    return y, y


def _reading_order(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group blocks with overlapping vertical boxes into rows, then order each row left-to-right."""
    positioned = []
    for block in blocks:
        top, bottom = _box_vertical_bounds(block)
        positioned.append((top, bottom, float(block.get("x", 0)), block))
    positioned.sort(key=lambda item: ((item[0] + item[1]) / 2, item[2]))

    lines: list[list[tuple[float, float, float, dict[str, Any]]]] = []
    for item in positioned:
        top, bottom, _, _ = item
        matching_line = next(
            (
                line
                for line in lines
                if (
                    min(bottom, max(entry[1] for entry in line))
                    - max(top, min(entry[0] for entry in line))
                )
                >= 0.5 * min(
                    bottom - top,
                    max(entry[1] for entry in line) - min(entry[0] for entry in line),
                )
                and bottom > top
                and max(entry[1] for entry in line) > min(entry[0] for entry in line)
            ),
            None,
        )
        if matching_line is None:
            lines.append([item])
        else:
            matching_line.append(item)

    lines.sort(key=lambda line: median((item[0] + item[1]) / 2 for item in line))
    return [
        item[3]
        for line in lines
        for item in sorted(line, key=lambda entry: entry[2])
    ]


class PaddleOCREngine:
    def __init__(self) -> None:
        os.environ.setdefault("FLAGS_use_mkldnn", "0")
        try:
            import paddle

            paddle.set_flags({"FLAGS_use_mkldnn": False, "FLAGS_enable_pir_api": False})
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError("Install the optional 'ml' dependencies to process scanned documents") from exc
        try:
            self._engine = PaddleOCR(
                lang="en",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
                enable_mkldnn=False,
                enable_hpi=False,
            )
        except TypeError:
            self._engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False, enable_mkldnn=False, ir_optim=False)

    def extract(self, image: Any) -> list[dict[str, Any]]:
        try:
            result = self._engine.predict(image) if hasattr(self._engine, "predict") else self._engine.ocr(image, cls=True)
        except Exception as exc:
            raise RuntimeError(
                "PaddleOCR could not run on this machine. Reinstall matching OCR packages with "
                "'.venv\\Scripts\\python.exe -m pip install --force-reinstall paddleocr==3.3.0 paddlepaddle==3.3.1'."
            ) from exc
        blocks: list[dict[str, Any]] = []
        for item in result or []:
            data = item.json if hasattr(item, "json") else item
            if isinstance(data, str):
                import json

                data = json.loads(data)
            if isinstance(data, dict) and "res" in data:
                data = data["res"]
            texts = data.get("rec_texts", []) if isinstance(data, dict) else []
            scores = data.get("rec_scores", []) if isinstance(data, dict) else []
            boxes = data.get("rec_boxes", []) if isinstance(data, dict) else []
            if texts:
                for index, text in enumerate(texts):
                    score = float(scores[index]) if index < len(scores) else 1.0
                    if score >= 0.4:
                        box = boxes[index] if index < len(boxes) else [0, 0, 0, 0]
                        box = box.tolist() if hasattr(box, "tolist") else list(box)
                        blocks.append({"text": str(text), "score": score, "box": box, "x": box[0], "y": box[1]})
                continue
            for line in item or []:
                if not line or len(line) < 2:
                    continue
                box, value = line
                text, score = value
                if float(score) < 0.4:
                    continue
                x = min(point[0] for point in box)
                y = min(point[1] for point in box)
                blocks.append({"text": text, "score": float(score), "box": box, "x": x, "y": y})
        return _reading_order(blocks)


class EasyOCREngine:
    def __init__(self) -> None:
        try:
            easyocr = import_module("easyocr")
        except ImportError as exc:
            raise RuntimeError("Install the optional 'ml' dependencies to use EasyOCR fallback") from exc
        self._engine = easyocr.Reader(["en"], gpu=False)

    def extract(self, image: Any) -> list[dict[str, Any]]:
        try:
            results = self._engine.readtext(image, detail=1)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
            raise RuntimeError("EasyOCR could not process this page.") from exc
        blocks: list[dict[str, Any]] = []
        for box, text, score in results:
            confidence = float(score)
            if confidence < 0.4:
                continue
            x = min(point[0] for point in box)
            y = min(point[1] for point in box)
            blocks.append(
                {
                    "text": str(text),
                    "score": confidence,
                    "box": box,
                    "x": x,
                    "y": y,
                }
            )
        return _reading_order(blocks)


class FallbackOCREngine:
    """Use PaddleOCR first and fall back to EasyOCR when it cannot read a page."""

    def __init__(self) -> None:
        self._paddle: PaddleOCREngine | None = None
        self._easy: EasyOCREngine | None = None
        self._paddle_init_error: Exception | None = None

    def extract(self, image: Any) -> tuple[str, list[dict[str, Any]]]:
        paddle_error = self._paddle_init_error
        if self._paddle is None and self._paddle_init_error is None:
            try:
                self._paddle = PaddleOCREngine()
            except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
                self._paddle_init_error = exc
                paddle_error = exc

        if self._paddle is not None:
            try:
                blocks = self._paddle.extract(image)
                if blocks:
                    return "paddleocr", blocks
                paddle_error = RuntimeError("PaddleOCR returned no readable text on this page.")
            except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
                # Inference errors may be page-specific; retry PaddleOCR on the next page.
                self._paddle = None
                paddle_error = exc

        try:
            if self._easy is None:
                self._easy = EasyOCREngine()
            blocks = self._easy.extract(image)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
            raise RuntimeError(
                "PaddleOCR failed and EasyOCR fallback is unavailable or failed. "
                f"PaddleOCR: {paddle_error}; EasyOCR: {exc}"
            ) from exc
        return "easyocr", blocks
