from pygame import Rect
from .settings import GameSettings
from dataclasses import dataclass
from enum import Enum
from typing import overload, TypedDict, Protocol

MouseBtn = int
Key = int

Direction = Enum('Direction', ['UP', 'DOWN', 'LEFT', 'RIGHT', 'NONE'])


@dataclass
class Position:
    x: float
    y: float

    def copy(self):
        return Position(self.x, self.y)

    def distance_to(self, other: "Position") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass
class PositionCamera:
    x: int
    y: int

    def copy(self):
        return PositionCamera(self.x, self.y)

    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)

    def transform_position(self, position: Position) -> tuple[int, int]:
        return (int(position.x) - self.x, int(position.y) - self.y)

    def transform_position_as_position(self, position: Position) -> Position:
        return Position(int(position.x) - self.x, int(position.y) - self.y)

    def transform_rect(self, rect: Rect) -> Rect:
        return Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)


@dataclass
class Teleport:
    pos: Position
    destination: str
    target_pos: Position
    @overload
    def __init__(self, x: int, y: int, destination: str) -> None: ...
    @overload
    def __init__(self, pos: Position, destination: str) -> None: ...

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], Position):
            self.pos = args[0]
            self.destination = args[1]
            self.target_pos = args[2]
        else:
            x, y, dest, target_pos = args
            self.pos = Position(x, y)
            self.destination = dest
            self.target_pos = target_pos

    def as_rect(self) -> Rect:
        return Rect(
            int(self.pos.x),
            int(self.pos.y),
            GameSettings.TILE_SIZE,
            GameSettings.TILE_SIZE
        )

    def collides_with(self, rect: Rect) -> bool:
        return self.as_rect().colliderect(rect)

    def to_dict(self):
        return {
            "x": int(self.pos.x) // GameSettings.TILE_SIZE,
            "y": int(self.pos.y) // GameSettings.TILE_SIZE,
            "destination": self.destination,
            "target_x": self.target_pos.x // GameSettings.TILE_SIZE,
            "target_y": self.target_pos.y // GameSettings.TILE_SIZE
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] *
                   GameSettings.TILE_SIZE, data["destination"],
                   Position(data["target_x"] * GameSettings.TILE_SIZE, data["target_y"] * GameSettings.TILE_SIZE))


class Monster(TypedDict):
    name: str
    hp: int
    max_hp: int
    level: int
    sprite_path: str


class Item(TypedDict):
    name: str
    count: int
    sprite_path: str
