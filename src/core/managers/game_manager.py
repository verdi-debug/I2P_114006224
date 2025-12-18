from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
import json
import os
import pygame as pg
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.entities.shop_npc import ShopNPC
    from src.data.bag import Bag


class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    shop_npc: dict[str, list[ShopNPC]]
    bag: "Bag"

    # Map properties
    current_map_key: str
    maps: dict[str, Map]

    # Changing Scene properties
    should_change_scene: bool
    next_map: str

    def __init__(self, maps: dict[str, Map], start_map: str,
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]],
                 shop_npc: dict[str, list[ShopNPC]],
                 bag: Bag | None = None):

        from src.data.bag import Bag

        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.shop_npc = shop_npc

        self.bag = bag if bag is not None else Bag([], [])

        self.places = {
            "ShopNPC": (18, 29),
            "Gym": (35, 25),
            "NewMap": (24, 25)
        }

        self.should_change_scene = False
        self.next_map = None
        self.next_pos = None

        # Global shop stock (shared by generic shop button)
        self.shop_items: list[dict] = self._generate_default_shop_items()
        self.shop_refresh_ms = 120_000  # 2 minutes
        self._time_until_shop_refresh = 0

    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]

    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers.get(self.current_map_key, [])

    @property
    def current_shop_npc(self) -> list[ShopNPC]:
        return self.shop_npc.get(self.current_map_key, [])

    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters

    def request_map_change(self, tp: Teleport) -> None:
        self.should_change_scene = True
        self.next_map = tp.destination
        self.next_pos = tp.target_pos.copy()

    def try_switch_map(self) -> None:
        if not self.should_change_scene:
            return

        self.current_map_key = self.next_map

        if self.player and self.next_pos:
            self.player.position.x = self.next_pos.x
            self.player.position.y = self.next_pos.y

            # Snap to tile grid
            self.player.position.x = (
                self.player.position.x // GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
            self.player.position.y = (
                self.player.position.y // GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE

        self.should_change_scene = False
        self.next_map = None
        self.next_pos = None

    def check_collision(self, rect: pg.Rect) -> bool:
        # Check map collision first
        if self.maps[self.current_map_key].check_collision(rect):
            return True

        # Check collision with enemy trainers
        for entity in self.current_enemy_trainers:
            if rect.colliderect(entity.animation.rect):
                return True

        # Check collision with shop NPCs
        for npc in self.current_shop_npc:
            if rect.colliderect(npc.animation.rect):
                return True

        return False

    def save(self, path: str) -> None:
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")

    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, object]:
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [t.to_dict()
                                       for t in self.enemy_trainers.get(key, [])]
            block["shop_npc"] = [npc.to_dict()
                                 for npc in self.shop_npc.get(key, [])]
            map_blocks.append(block)

        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player is not None else None,
            "bag": self.bag.to_dict(),
            "shop_state": {
                "items": self.shop_items,
                "time_until_refresh": self._time_until_shop_refresh
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.entities.shop_npc import ShopNPC
        from src.data.bag import Bag

        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}
        shop_npc_dict: dict[str, list[ShopNPC]] = {}

        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)

        current_map_key = data["current_map"]

        gm = cls(
            maps,
            current_map_key,
            None,          # player
            trainers,
            shop_npc_dict,     # shop NPCs
            bag=None
        )

        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            gm.enemy_trainers[m["path"]] = [
                EnemyTrainer.from_dict(t, gm)
                for t in m.get("enemy_trainers", [])
            ]

        Logger.info("Loading shop NPCs")
        for m in data["map"]:
            gm.shop_npc[m["path"]] = [
                ShopNPC.from_dict(npc, gm)
                for npc in m.get("shop_npc", [])
            ]

        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)

        Logger.info("Loading bag")
        gm.bag = Bag.from_dict(data.get("bag", {}))

        # Load shop state
        shop_state = data.get("shop_state", {})
        gm.shop_items = shop_state.get(
            "items", gm._generate_default_shop_items())
        gm._time_until_shop_refresh = shop_state.get(
            "time_until_refresh", 0)

        return gm

    def tick_shop(self, dt_ms: int) -> None:
        """Advance the global shop timer and restock when needed."""
        self._time_until_shop_refresh -= dt_ms
        if self._time_until_shop_refresh <= 0:
            self._restock_shop()
            self._time_until_shop_refresh = self.shop_refresh_ms

    def _restock_shop(self) -> None:
        """Restock default shop items (potion + pokeball only)."""
        self.shop_items = self._generate_default_shop_items()

    def _generate_default_shop_items(self) -> list[dict]:
        """Base stock shared by the general shop."""
        return [
            {"name": "Potion", "count": 5, "price": 30,
                "sprite_path": "ingame_ui/potion.png"},
            {"name": "Pokeball", "count": 5, "price": 50,
                "sprite_path": "ingame_ui/ball.png"},
        ]
