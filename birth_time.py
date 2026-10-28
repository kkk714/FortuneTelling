"""不依赖终端或网页的当地时间解析，供两种入口共用。"""

from datetime import timezone
from zoneinfo import ZoneInfo


def resolve_local_time(birth, zone_name):
    """返回当地钟点对应的真实时刻：空缺为 0 个，正常为 1 个，重复为 2 个。"""
    zone = ZoneInfo(zone_name)
    candidates = []
    seen = set()

    for fold in (0, 1):
        candidate = birth.replace(tzinfo=zone, fold=fold)
        utc_time = candidate.astimezone(timezone.utc)
        restored = utc_time.astimezone(zone)

        if restored.replace(tzinfo=None) == birth and utc_time not in seen:
            candidates.append(candidate)
            seen.add(utc_time)

    return candidates
