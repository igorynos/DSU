"""Pure helpers used by UI widgets — no Flet imports here."""

from __future__ import annotations


def format_status_text(online: bool) -> str:
    return "online" if online else "offline"


def format_serial_short(s_num: str, max_chars: int = 14) -> str:
    if not s_num:
        return ""
    if len(s_num) <= max_chars:
        return s_num
    return s_num[:max_chars] + "…"


def matches_filter(device, query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True
    parts = (
        getattr(device, "name", "") or "",
        getattr(device, "ip", "") or "",
        getattr(device, "s_num", "") or "",
    )
    return any(q in p.lower() for p in parts)
