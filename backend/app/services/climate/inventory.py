"""Bounded file-presence inventory. This never admits climate evidence."""

from pathlib import Path
import stat

from app.schemas.planting_window import DistrictCacheEntry, DistrictCacheInventory
from app.services.m1_reference import geography

MAX_INDEX_BYTES = 2 * 1024 * 1024


def district_cache_inventory(root: Path) -> DistrictCacheInventory:
    root = root.resolve()
    entries = []
    for district in sorted(geography().districts.values(), key=lambda item: item.code):
        status = "missing"
        try:
            index = (root / district.code / "bundle.json").resolve()
            if not index.is_relative_to(root):
                status = "unreadable"
            else:
                info = index.stat()
                status = ("cached" if stat.S_ISREG(info.st_mode)
                          and 0 < info.st_size <= MAX_INDEX_BYTES else "unreadable")
        except FileNotFoundError:
            pass
        except (OSError, RuntimeError):
            status = "unreadable"
        entries.append(DistrictCacheEntry(
            district_code=district.code, name=district.name, name_bn=district.name_bn,
            status=status,
        ))
    return DistrictCacheInventory(
        districts=entries, cached_count=sum(item.status == "cached" for item in entries),
    )
