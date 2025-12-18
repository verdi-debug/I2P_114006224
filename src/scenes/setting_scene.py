import pygame as pg
from src.scenes.scene import Scene
from src.sprites import BackgroundSprite
from src.interface.components import (Button, VolumeSlider, MuteCheckbox)
from src.utils import GameSettings
from src.core.services import scene_manager, input_manager
from typing import override


class SettingScene(Scene):
    background: BackgroundSprite
    back_button: Button

    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite(
            "backgrounds/background2.png")

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2

        # Back button to return to menu
        self.back_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            px - 50, py + 200, 100, 100,
            lambda: scene_manager.change_scene("menu")
        )

        # Vol Slider
        self.volume_slider = VolumeSlider(
            x=px - 150,
            y=py - 50,
            width=300,
            height=20
        )

        # Mute Checkbox
        self.mute_checkbox = MuteCheckbox(
            x=px - 150,
            y=py - 10,
            size=50
        )

    @override
    def enter(self) -> None:
        pass

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        self.back_button.update(dt)
        self.volume_slider.update(dt)
        self.mute_checkbox.update(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.back_button.draw(screen)
        self.volume_slider.draw(screen)
        self.mute_checkbox.draw(screen)
