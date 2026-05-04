"""Color palette for light and dark themes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    bg: str
    panel: str
    border: str
    text: str
    text_dim: str
    accent: str
    online: str
    offline: str
    success: str
    error: str


DARK = Palette(
    bg="#1e1e1e", panel="#252525", border="#333333",
    text="#dddddd", text_dim="#888888",
    accent="#4a9eff",
    online="#4ade80", offline="#666666",
    success="#4ade80", error="#ef4444",
)

LIGHT = Palette(
    bg="#fafafa", panel="#ffffff", border="#e0e0e0",
    text="#1a1a1a", text_dim="#777777",
    accent="#2563eb",
    online="#16a34a", offline="#9ca3af",
    success="#16a34a", error="#dc2626",
)


def palette_for(mode: str) -> Palette:
    """Return palette for current theme. mode: 'dark' | 'light'."""
    return DARK if mode == "dark" else LIGHT
