from __future__ import annotations
import pygame as pg
from src.core.services import input_manager
from src.utils import GameSettings
from src.core.services import sound_manager
from typing import override
from .component import UIComponent


class VolumeSlider(UIComponent):
    """Component for volume slider control."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 300,
        height: int = 20
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Volume slider properties
        self.slider_rect = pg.Rect(x, y, width, height)
        self.slider_handle_radius = 10
        self.slider_handle_x = x + int(GameSettings.AUDIO_VOLUME * width)
        self.dragging = False

    def _update_volume(self, volume: float):
        """Update the volume setting and apply it to the sound manager."""
        volume = max(0.0, min(1.0, volume))
        GameSettings.AUDIO_VOLUME = volume

        # Update sound manager
        if hasattr(sound_manager, 'set_volume'):
            sound_manager.set_volume(volume)

        # Update current BGM if playing
        if hasattr(sound_manager, 'current_bgm') and sound_manager.current_bgm:
            muted = getattr(sound_manager, 'muted', False)
            sound_manager.current_bgm.set_volume(volume if not muted else 0.0)

    @override
    def update(self, dt: float) -> None:
        mouse_pos = input_manager.mouse_pos
        mouse_pressed = input_manager.mouse_pressed(1)
        mouse_held = input_manager.mouse_down(1)

        # Handle volume slider
        handle_rect = pg.Rect(
            self.slider_handle_x - self.slider_handle_radius,
            self.y - self.slider_handle_radius // 2,
            self.slider_handle_radius * 2,
            self.height + self.slider_handle_radius
        )

        if mouse_pressed and handle_rect.collidepoint(mouse_pos):
            self.dragging = True
        elif mouse_pressed and self.slider_rect.collidepoint(mouse_pos):
            relative_x = mouse_pos[0] - self.x
            volume = relative_x / self.width
            self._update_volume(volume)
            self.slider_handle_x = self.x + int(volume * self.width)
            self.dragging = True

        if self.dragging:
            if mouse_held:
                # Update slider position based on mouse
                relative_x = mouse_pos[0] - self.x
                volume = relative_x / self.width
                self._update_volume(volume)
                self.slider_handle_x = self.x + int(volume * self.width)
                # Clamp handle position
                self.slider_handle_x = max(self.x, min(
                    self.x + self.width, self.slider_handle_x))
            else:
                self.dragging = False

    @override
    def draw(self, screen: pg.Surface) -> None:
        # Draw volume slider track
        pg.draw.rect(screen, (100, 100, 100), self.slider_rect)
        pg.draw.rect(screen, (200, 200, 200), self.slider_rect, 2)

        filled_width = int(GameSettings.AUDIO_VOLUME * self.width)
        if filled_width > 0:
            filled_rect = pg.Rect(self.x, self.y, filled_width, self.height)
            pg.draw.rect(screen, (100, 200, 100), filled_rect)

        handle_y = self.y + self.height // 2
        handle_color = (150, 150, 150) if self.dragging else (200, 200, 200)
        pg.draw.circle(screen, handle_color, (self.slider_handle_x,
                       handle_y), self.slider_handle_radius)
        pg.draw.circle(screen, (255, 255, 255), (self.slider_handle_x,
                       handle_y), self.slider_handle_radius, 2)
