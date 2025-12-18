from __future__ import annotations
import pygame as pg
from dataclasses import dataclass
from typing import override

from src.entities.entity import Entity
from src.utils import GameSettings, Direction, Position, PositionCamera
from src.sprites import Animation, Sprite
from src.core import GameManager
from src.core.services import input_manager


@dataclass
class IdleMovement:
    def update(self, npc: "ShopNPC", dt: float) -> None:
        return


class ShopNPC(Entity):
    max_tiles: int
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    los_direction: Direction
    animation: Animation

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        facing: Direction,
        animation_path: str,
        n_keyframes: int,
        rows: list[str] = ["down", "left", "right", "up"],
        max_tiles: int = 2,
    ):
        super().__init__(x, y, game_manager)

        self.max_tiles = max_tiles
        self._movement = IdleMovement()
        self._set_direction(facing)

        # Main animation
        self.animation = Animation(
            image_path=animation_path,
            rows=rows,
            n_keyframes=n_keyframes,
            size=(GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
            loop=0.5  # Half-second loop
        )
        self.animation.update_pos(self.position)

        # Warning sign
        self.warning_sign = Sprite(
            "exclamation.png",
            (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2)
        )
        self.warning_sign.update_pos(
            Position(
                x + GameSettings.TILE_SIZE // 4,
                y - GameSettings.TILE_SIZE // 2
            )
        )

        self.detected = False
        self.shop_items = data = [
            {
                "sprite_path": "ingame_ui/potion.png",
                "name": "Potion",
                "price": 30,
                "count": 10
            },
            {
                "sprite_path": "ingame_ui/ball.png",
                "name": "Pokeball",
                "price": 50,
                "count": 10
            }
        ]

    @override
    def update(self, dt: float) -> None:
        self._movement.update(self, dt)
        self._has_los_to_player()
        self.animation.update(dt)
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        self.animation.draw(screen, camera)

        if self.detected:
            self.warning_sign.draw(screen, camera)

        """if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()
            pg.draw.rect(screen, (255, 255, 0),
                         camera.transform_rect(los_rect), 1)"""

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction

        if direction == Direction.RIGHT:
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")

        self.los_direction = self.direction

    def _get_los_rect(self) -> pg.Rect:
        size = GameSettings.TILE_SIZE

        if self.los_direction == Direction.RIGHT:
            return pg.Rect(self.position.x + size, self.position.y, size * self.max_tiles, size)
        if self.los_direction == Direction.LEFT:
            return pg.Rect(self.position.x - size * self.max_tiles, self.position.y, size * self.max_tiles, size)
        if self.los_direction == Direction.DOWN:
            return pg.Rect(self.position.x, self.position.y + size, size, size * self.max_tiles)
        # UP
        return pg.Rect(self.position.x, self.position.y - size * self.max_tiles, size, size * self.max_tiles)

    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return

        los_rect = self._get_los_rect()
        player_rect = player.animation.rect.copy()
        self.detected = los_rect.colliderect(player_rect)

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "ShopNPC":
        x = data["x"] * GameSettings.TILE_SIZE
        y = data["y"] * GameSettings.TILE_SIZE

        facing_raw = data.get("facing", "DOWN")
        facing = Direction[facing_raw] if isinstance(
            facing_raw, str) else facing_raw

        max_tiles = data.get("max_tiles", 2)
        animation_path = data.get("animation_path", "character/ow5.png")
        n_keyframes = data.get("n_keyframes", 4)
        rows = data.get("rows", ["down", "left", "right", "up"])

        npc = cls(x, y, game_manager, facing,
                  animation_path, n_keyframes, rows, max_tiles)
        npc.shop_items = data.get("shop_items", npc.shop_items)
        return npc

    @override
    def to_dict(self) -> dict[str, object]:
        base = super().to_dict()
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        base["n_keyframes"] = self.animation.n_keyframes
        base["rows"] = list(self.animation.animations.keys())
        base["shop_items"] = self.shop_items
        return base
