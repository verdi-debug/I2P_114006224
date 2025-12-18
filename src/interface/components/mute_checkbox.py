from __future__ import annotations
import pygame as pg
from src.core.services import input_manager
from src.core.services import sound_manager
from typing import override
from .component import UIComponent


class MuteCheckbox(UIComponent):
    """Component for mute audio checkbox."""

    def __init__(
        self,
        x: int,
        y: int,
        size: int = 25
    ):
        self.x = x
        self.y = y
        self.size = size
        self.checkbox_rect = pg.Rect(x, y, size, size)
        self.muted = getattr(sound_manager, 'muted', False)

    def _toggle_mute(self):
        """Toggle mute state."""
        self.muted = not self.muted
        if hasattr(sound_manager, 'set_muted'):
            sound_manager.set_muted(self.muted)
        elif self.muted:
            sound_manager.pause_all()
        else:
            sound_manager.resume_all()

    def update_muted_state(self):
        """Sync muted state with sound manager."""
        self.muted = getattr(sound_manager, 'muted', False)

    @override
    def update(self, dt: float) -> None:
        # Sync muted state with sound manager
        self.update_muted_state()

        mouse_pos = input_manager.mouse_pos
        mouse_pressed = input_manager.mouse_pressed(1)

        if mouse_pressed and self.checkbox_rect.collidepoint(mouse_pos):
            self._toggle_mute()

    @override
    def draw(self, screen: pg.Surface) -> None:
        pg.draw.rect(screen, (100, 100, 100), self.checkbox_rect)
        pg.draw.rect(screen, (200, 200, 200), self.checkbox_rect, 2)

        if self.muted:
            x1 = self.checkbox_rect.x + 5
            y1 = self.checkbox_rect.y + 5
            x2 = self.checkbox_rect.x + self.size - 5
            y2 = self.checkbox_rect.y + self.size - 5
            # For the diagonals
            pg.draw.line(screen, (255, 255, 255), (x1, y1), (x2, y2), 3)
            pg.draw.line(screen, (255, 255, 255), (x2, y1), (x1, y2), 3)
