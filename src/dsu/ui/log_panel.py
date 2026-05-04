"""Collapsible log panel — stores entries, renders list, supports clear/copy."""

from __future__ import annotations

import time
from typing import Literal

import flet as ft

LogLevel = Literal["info", "warn", "error"]


class LogPanel:
    def __init__(self) -> None:
        self._entries: list[tuple[float, LogLevel, str]] = []
        self._list = ft.ListView(spacing=2, padding=8, expand=True)

        clear_btn = ft.TextButton(
            "Clear", icon=ft.Icons.DELETE_OUTLINE,
            on_click=lambda _: self.clear())
        copy_btn = ft.TextButton(
            "Copy all", icon=ft.Icons.CONTENT_COPY,
            on_click=self._copy_all)

        self.control = ft.Container(
            visible=False,
            height=180,
            border=ft.border.only(top=ft.BorderSide(1, "#333")),
            bgcolor="#1a1a1a",
            content=ft.Column(
                controls=[
                    ft.Row(controls=[
                        ft.Text("Log", size=11, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        clear_btn, copy_btn,
                    ]),
                    self._list,
                ],
                expand=True,
            ),
        )

    def toggle(self) -> None:
        self.control.visible = not self.control.visible
        if self.control.page is not None:
            self.control.update()

    def add(self, text: str, level: LogLevel = "info") -> None:
        self._entries.append((time.time(), level, text))
        self._list.controls.append(self._render_entry(self._entries[-1]))
        if self._list.page is not None:
            self._list.update()

    def clear(self) -> None:
        self._entries.clear()
        self._list.controls.clear()
        if self._list.page is not None:
            self._list.update()

    def _copy_all(self, _e: ft.ControlEvent) -> None:
        if _e.page is None:
            return
        text = "\n".join(self._format(entry) for entry in self._entries)
        _e.page.set_clipboard(text)

    def _render_entry(self, entry: tuple[float, LogLevel, str]) -> ft.Text:
        return ft.Text(self._format(entry), size=10,
                       color=self._color_for(entry[1]),
                       font_family="monospace")

    @staticmethod
    def _format(entry: tuple[float, LogLevel, str]) -> str:
        ts = time.strftime("%H:%M:%S", time.localtime(entry[0]))
        return f"[{ts}] {entry[1]:<5} — {entry[2]}"

    @staticmethod
    def _color_for(level: LogLevel) -> str:
        return {"info": "#dddddd", "warn": "#facc15", "error": "#ef4444"}[level]
