import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        pass

    @property
    def monsters(self) -> list[Monster]:
        return self._monsters_data

    @property
    def items(self) -> list[Item]:
        return self._items_data

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    def add_coins(self, amount: int) -> None:
        for item in self.items:
            if item["name"] == "Coins":
                item["count"] += amount
                return

        self.items.append({
            "name": "Coins",
            "count": amount,
            "sprite_path": "ingame_ui/coin.png"
        })

    def spend_coins(self, amount: int) -> None:
        for item in self.items:
            if item["name"] == "Coins":
                if item["count"] >= amount:
                    item["count"] -= amount
                    return True
                else:
                    return False
        return False

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag
