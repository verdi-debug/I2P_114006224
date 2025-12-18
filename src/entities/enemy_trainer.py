from __future__ import annotations
import pygame as pg
from enum import Enum
from dataclasses import dataclass
from typing import override

from src.utils.definition import Monster
from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.core.services import input_manager, scene_manager
from src.utils import GameSettings, Direction, Position, PositionCamera


class EnemyTrainerClassification(Enum):
    STATIONARY = "stationary"


@dataclass
class IdleMovement:
    def update(self, enemy: "EnemyTrainer", dt: float) -> None:
        return


class EnemyTrainer(Entity):
    classification: EnemyTrainerClassification
    max_tiles: int | None
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    los_direction: Direction
    monsters: list[Monster]

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        classification: EnemyTrainerClassification = EnemyTrainerClassification.STATIONARY,
        max_tiles: int | None = 2,
        facing: Direction | None = None,
        monsters: list[Monster] | None = None
    ) -> None:
        super().__init__(x, y, game_manager)

        self.classification = classification
        self.max_tiles = max_tiles

        if classification == EnemyTrainerClassification.STATIONARY:
            self._movement = IdleMovement()
            if facing is None:
                raise ValueError(
                    "Idle EnemyTrainer requires a 'facing' Direction at instantiation")
            self._set_direction(facing)
        else:
            raise ValueError("Invalid classification")

        self.monsters = monsters if monsters is not None else []

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

    @override
    def update(self, dt: float) -> None:
        self._movement.update(self, dt)
        self._has_los_to_player()

        if self.detected and input_manager.key_pressed(pg.K_SPACE):
            battle_scene = scene_manager._scenes["battle_scene"]
            battle_scene.set_enemy_trainer(self)
            battle_scene.set_game_manager(self.game_manager)
            scene_manager.change_scene("battle_scene")

        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)

        if self.detected:
            self.warning_sign.draw(screen, camera)

        # if GameSettings.DRAW_HITBOXES:
            # los_rect = self._get_los_rect()
            # if los_rect is not None:
            # pg.draw.rect(
            # screen,
            # (255, 255, 0),
            # camera.transform_rect(los_rect),
            # 1
            # )

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

    def _get_los_rect(self) -> pg.Rect | None:
        """Creates line-of-sight rectangle based on direction."""

        if self.los_direction == Direction.RIGHT:
            x = self.position.x + GameSettings.TILE_SIZE
            y = self.position.y
            los_rec = pg.Rect(
                x, y,
                GameSettings.TILE_SIZE * self.max_tiles,
                GameSettings.TILE_SIZE
            )

        elif self.los_direction == Direction.LEFT:
            x = self.position.x - GameSettings.TILE_SIZE * self.max_tiles
            y = self.position.y
            los_rec = pg.Rect(
                x, y,
                GameSettings.TILE_SIZE * self.max_tiles,
                GameSettings.TILE_SIZE
            )

        elif self.los_direction == Direction.DOWN:
            x = self.position.x
            y = self.position.y + GameSettings.TILE_SIZE
            los_rec = pg.Rect(
                x, y,
                GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE * self.max_tiles
            )

        else:  # UP
            x = self.position.x
            y = self.position.y - GameSettings.TILE_SIZE * self.max_tiles
            los_rec = pg.Rect(
                x, y,
                GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE * self.max_tiles
            )

        return los_rec

    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return

        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return

        player_rect = player.animation.rect.copy()

        if los_rect.colliderect(player_rect):
            self.detected = True
            return

        self.detected = False

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "EnemyTrainer":
        classification = EnemyTrainerClassification(
            data.get("classification", "stationary")
        )

        max_tiles = data.get("max_tiles")
        facing_val = data.get("facing")

        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val

        if facing is None and classification == EnemyTrainerClassification.STATIONARY:
            facing = Direction.DOWN

        monsters = data["monsters"]

        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            classification,
            max_tiles,
            facing,
            monsters
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["classification"] = self.classification.value
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        base["monsters"] = self.monsters
        return base
