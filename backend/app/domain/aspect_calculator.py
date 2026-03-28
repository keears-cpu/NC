from __future__ import annotations

from ..schemas import Aspect, ChartBody
from .house_assignment import normalize_lon

ASPECTS = {
    "conjunction": (0, 8),
    "sextile": (60, 5),
    "square": (90, 6),
    "trine": (120, 6),
    "opposition": (180, 8),
}


def compute_aspects(items: list[ChartBody]) -> list[Aspect]:
    aspects: list[Aspect] = []
    next_id = 1
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            delta = abs(normalize_lon(right.lon - left.lon))
            delta = min(delta, 360 - delta)
            for aspect_name, (target, orb) in ASPECTS.items():
                diff = abs(delta - target)
                if diff <= orb:
                    degree = int(diff)
                    minute = round((diff - degree) * 60)
                    aspects.append(
                        Aspect(
                            id=f"asp_{next_id:03d}",
                            point_a=left.id,
                            point_b=right.id,
                            aspect_type=aspect_name,
                            orb_text=f"{degree}°{minute:02d}’",
                        )
                    )
                    next_id += 1
                    break
    return aspects
