"""Line rebuilding by height-based clustering; keeps Block objects."""

from ml.vision.config import DEFAULT_CONFIG, OCRConfig
from ml.vision.schemas import Block


def _cy(b: Block) -> float:
    return (b.bbox[1] + b.bbox[3]) / 2.0


def group_into_lines(
    blocks: list[Block], config: OCRConfig = DEFAULT_CONFIG
) -> list[list[Block]]:
    if not blocks:
        return []

    heights = sorted(max(1.0, b.bbox[3] - b.bbox[1]) for b in blocks)
    tolerance = config.row_height_ratio * heights[len(heights) // 2]

    ordered = sorted(blocks, key=_cy)
    lines: list[list[Block]] = []
    current: list[Block] = [ordered[0]]

    for b in ordered[1:]:
        current_avg = sum(_cy(x) for x in current) / len(current)
        if abs(_cy(b) - current_avg) <= tolerance:
            current.append(b)
        else:
            lines.append(sorted(current, key=lambda x: x.bbox[0]))
            current = [b]

    lines.append(sorted(current, key=lambda x: x.bbox[0]))
    return lines


def lines_to_text(lines: list[list[Block]]) -> list[str]:
    return [" ".join(b.text for b in line) for line in lines]
