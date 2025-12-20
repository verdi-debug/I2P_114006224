from __future__ import annotations
import pygame as pg
from src.utils import Position, PositionCamera, Direction, GameSettings, Logger
from .entity import Entity
from src.core.services import input_manager
from src.core import GameManager
import math
from typing import override
from src.entities.enemy_trainer import EnemyTrainer


class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self.player_is_navigating = False

    @property
    def rect(self) -> pg.Rect:
        r = self.animation.rect.copy()
        r.topleft = (self.position.x, self.position.y)
        return r

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0)
        raw_x = 0
        raw_y = 0

        # --- INPUT ---
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
            raw_x = -1
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
            raw_x = 1
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
            raw_y = -1
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1
            raw_y = 1

        if raw_x > 0:
            if self.direction != Direction.RIGHT:
                self.direction = Direction.RIGHT
                self.animation.switch("right")
        elif raw_x < 0:
            if self.direction != Direction.LEFT:
                self.direction = Direction.LEFT
                self.animation.switch("left")
        elif raw_y > 0:
            if self.direction != Direction.DOWN:
                self.direction = Direction.DOWN
                self.animation.switch("down")
        elif raw_y < 0:
            if self.direction != Direction.UP:
                self.direction = Direction.UP
                self.animation.switch("up")

        magnitude = math.sqrt(dis.x**2 + dis.y**2)
        if magnitude > 0:
            dis.x /= magnitude
            dis.y /= magnitude
            dis.x *= self.speed * dt
            dis.y *= self.speed * dt

        is_moving = raw_x != 0 or raw_y != 0

        # Move X
        player_rect_x = self.animation.rect.copy()
        player_rect_x.topleft = (self.position.x + dis.x, self.position.y)
        if not self.game_manager.check_collision(player_rect_x):
            self.position.x += dis.x
        else:
            self.position.x = Player._snap_to_grid(self.position.x)

        # Move Y
        player_rect_y = self.animation.rect.copy()
        player_rect_y.topleft = (self.position.x, self.position.y + dis.y)
        if not self.game_manager.check_collision(player_rect_y):
            self.position.y += dis.y
        else:
            self.position.y = Player._snap_to_grid(self.position.y)

        # --- TELEPORTATION ---
        player_rect = self.animation.rect.copy()
        player_rect.topleft = (self.position.x, self.position.y)
        tp = self.game_manager.current_map.check_teleport(player_rect)
        if tp is not None and not self.player_is_navigating:
            self.game_manager.request_map_change(tp)

        self.game_manager.try_switch_map()

        super().update(dt)
        self.animation.update_pos(self.position)
        self.animation.update(dt)
        self.last_is_moving = is_moving

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)

    @property
    @override
    def camera(self) -> PositionCamera:
        height = self.game_manager.player.animation.rect.height
        width = self.game_manager.player.animation.rect.width
        return PositionCamera(
            int(self.position.x) - GameSettings.SCREEN_WIDTH // 2 + width // 2,
            int(self.position.y) - GameSettings.SCREEN_HEIGHT // 2 + height // 2
        )

    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:

        player = cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager
        )

        if "direction" in data:
            player.direction = Direction[data["direction"]]
            player.animation.switch(player.direction.name.lower())
        return player

    @override
    def to_dict(self) -> dict[str, object]:
        return {
            "x": self.position.x / GameSettings.TILE_SIZE,
            "y": self.position.y / GameSettings.TILE_SIZE,
            "direction": self.direction.name,
            "is_moving": self.last_is_moving
        }
