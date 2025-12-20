import pygame as pg
import pytmx
import random
from collections import deque
from src.scenes.scene import Scene
from src.core.services import scene_manager, input_manager
from src.entities.shop_npc import ShopNPC
from src.entities.player import Player
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.interface.components import (
    Button,
    VolumeSlider,
    MuteCheckbox,
    BagItemList,
)
from src.interface.components.shop_item_list import ShopItemList
from src.interface.components.shop_item_row import ShopItemRow
from src.interface.components.chat_overlay import ChatOverlay
from typing import override
from src.sprites import Sprite, Animation


class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    settings_button: Button
    volume_slider: VolumeSlider
    mute_checkbox: MuteCheckbox
    save_button: Button
    load_button: Button

    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager

        # Load Map
        self.tmx_data = pytmx.util_pygame.load_pygame(
            "assets/maps/map.tmx")

        # Bush Rects
        self.bush_rects = []

        # Chat Overlay
        self._online_last_pos: dict[int, tuple[float, float]] = {}
        self._chat_bubbles: dict[int, tuple[str, float]] = {}
        self._last_chat_id_seen: int = 0
        self._chat_messages: deque[dict] = deque(maxlen=100)

        # Get the bush layer
        bush_layer = self.tmx_data.get_layer_by_name("PokemonBush")

        for x, y, gid in bush_layer:
            if gid <= 30:
                continue  # Skip empty tiles
            tile = self.tmx_data.get_tile_image_by_gid(gid)
            if tile:

                rect = pg.Rect(
                    x * GameSettings.TILE_SIZE,
                    y * GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE
                )

                self.bush_rects.append(rect)

        # Setting Button
        self.settings_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            10, 10, 100, 100,
            on_click=self.open_settings
        )

        # Backpack Button
        self.backpack_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            120, 10, 100, 100,
            on_click=self.open_backpack
        )

        # Shop Button
        self.shop_button = Button(
            "UI/button_shop.png", "UI/button_shop_hover.png",
            230, 10, 100, 100,
            on_click=self.open_shop
        )

        # Navigation Button 1
        self.place1_button = Button(
            "UI/button_nav1 (1).png", "UI/button_nav1 (1).png",
            10, 120, 50, 50,
            on_click=lambda: self.select_place("ShopNPC")
        )
        # Navigation Button 2
        self.place2_button = Button(
            "UI/button_nav2 (1).png", "UI/button_nav2 (1).png",
            70, 120, 50, 50,
            on_click=lambda: self.select_place("Gym")
        )
        # Navigation Button 3
        self.place3_button = Button(
            "UI/button_nav3 (1).png", "UI/button_nav3 (1).png",
            130, 120, 50, 50,
            on_click=lambda: self.select_place("NewMap")
        )

        # Navigation State
        self.navigation_path: list[tuple[int, int]] = []
        self.is_navigating: bool = False
        self.navigation_goal: tuple[int, int] | None = None
        self.navigation_index: int = 0

        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
            self.chat_overlay = ChatOverlay(
                send_callback=self.send_message,
                get_messages=self.get_messages
            )

        else:
            self.online_manager = None
            self.chat_overlay = None
        self.sprite_online = Sprite(
            "ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        self.remote_players: dict[int, dict] = {}

        # Overlay flag for Settings
        self.settings_overlay = False

        # Overlay flag for Backpack
        self.backpack_overlay = False

        # Overlay flag for Shop
        self.shop_overlay = False

        # Overlay flag for ShopNPC
        self.shop_npc_overlay = False

        screen_w, screen_h = GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT

        # Settings overlay box
        panel_w, panel_h = 400, 300
        self.overlay_rect = pg.Rect(
            (screen_w - panel_w) // 2,
            (screen_h - panel_h) // 2,
            panel_w,
            panel_h
        )
        self.shop_rect = pg.Rect(
            (screen_w - panel_w) // 2,
            (screen_h - panel_h) // 2,
            panel_w,
            panel_h
        )
        self.shop_npc_rect = pg.Rect(
            (screen_w - panel_w) // 2,
            (screen_h - panel_h) // 2,
            panel_w,
            panel_h
        )

        # ShopItemRow for npc
        self.shop_npc_list = ShopItemList(
            self.overlay_rect.x + 20,
            self.overlay_rect.y + 80,
            self.overlay_rect.width - 40,
            self.overlay_rect.height - 140,
            clickable_buy=False  # buy handled by dedicated button
        )
        # Buy button for NPC shop (placed beside back button)
        self.buy_button_shop_npc = Button(
            "UI/button_shop.png", "UI/button_shop_hover.png",
            self.overlay_rect.centerx + 60,
            self.overlay_rect.bottom - 60,
            100, 50,
            on_click=self._handle_npc_purchase
        )
        self.current_npc_item: dict | None = None
        self.next_refresh_time = 0
        if self.game_manager.shop_items:
            self.refresh_shop_item()
        # Battle flag init
        self.battle_triggered = False

        # Backpack overlay box
        bag_w, bag_h = 520, 340
        self.backpack_rect = pg.Rect(
            (screen_w - bag_w) // 2,
            (screen_h - bag_h) // 2,
            bag_w,
            bag_h
        )
        # Shop overlay box
        panel_w, panel_h = 400, 300
        self.overlay_rect = pg.Rect(
            (screen_w - panel_w) // 2,
            (screen_h - panel_h) // 2,
            panel_w,
            panel_h
        )

        # Shop NPC overlay box
        panel_w, panel_h = 400, 300
        self.overlay_rect = pg.Rect(
            (screen_w - panel_w) // 2,
            (screen_h - panel_h) // 2,
            panel_w,
            panel_h
        )

        # Audio Settings Components
        audio_x = self.overlay_rect.x + 50
        audio_y = self.overlay_rect.y + 90
        self.volume_slider = VolumeSlider(
            audio_x, audio_y, width=300, height=20)
        self.mute_checkbox = MuteCheckbox(audio_x, audio_y + 40, size=25)

        # Save and Load Buttons
        button_y = self.overlay_rect.y + 180
        self.save_button = Button(
            "UI/button_save.png", "UI/button_save_hover.png",
            self.overlay_rect.x + 50,
            button_y,
            100, 50,
            on_click=self.save_game
        )
        self.load_button = Button(
            "UI/button_load.png", "UI/button_load_hover.png",
            self.overlay_rect.right - 150,
            button_y,
            100, 50,
            on_click=self.load_game
        )

        # Back Button
        self.back_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.overlay_rect.centerx - 50,
            self.overlay_rect.bottom - 60,
            100, 50,
            on_click=self.close_settings,
        )

        # backpack item list + back button
        list_margin = 20
        list_top = self.backpack_rect.y + 80
        list_height = self.backpack_rect.height - 140
        self.bag_item_list = BagItemList(
            self.backpack_rect.x + list_margin,
            list_top,
            self.backpack_rect.width - (list_margin * 2),
            list_height
        )

        # Back Button for Backpack
        self.back_button_backpack = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.backpack_rect.centerx - 50,
            self.backpack_rect.bottom - 60,
            100, 50,
            on_click=self.close_backpack

        )
        # Shop Item List for Normal Shop
        self.shop_item_list = ShopItemList(
            self.overlay_rect.x + 20,
            self.overlay_rect.y + 80,
            self.overlay_rect.width - 40,
            self.overlay_rect.height - 140
        )
        # Connect provider so the list can actually pull items
        self.shop_item_list.set_provider(self._get_shop_stock)
        self.shop_item_list.force_refresh()
        # Back Button for Shop
        self.back_button_shop = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.overlay_rect.centerx - 50,
            self.overlay_rect.bottom - 60,
            100, 50,
            on_click=self.close_shop,
        )
        # Back Button for Shop NPC
        self.back_button_shop_npc = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.overlay_rect.centerx - 50,
            self.overlay_rect.bottom - 60,
            100, 50,
            on_click=self.close_shop_npc
        )

        self._refresh_bag_items()

        self.walkable_grid = [
            [
                not self.game_manager.current_map.check_collision(
                    pg.Rect(x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                )
                for y in range(self.game_manager.current_map.tmxdata.height)
            ]
            for x in range(self.game_manager.current_map.tmxdata.width)
        ]

    def open_settings(self):
        self.settings_overlay = True

    def close_settings(self):
        self.settings_overlay = False

    def open_backpack(self):
        self._refresh_bag_items()
        self.backpack_overlay = True

    def close_backpack(self):
        self.backpack_overlay = False

    def open_shop(self):
        self.shop_overlay = True
        # Prefer the nearby NPC inventory if present; otherwise fall back to default shop stock
        if self.game_manager.current_shop_npc:
            npc = self.game_manager.current_shop_npc[0]
            if npc.shop_items:
                self.shop_item_list.set_provider(lambda: npc.shop_items)
                self.shop_item_list.force_refresh()
                return
        self.shop_item_list.set_provider(self._get_shop_stock)
        self.shop_item_list.force_refresh()

    def close_shop(self):
        self.shop_overlay = False

    def open_shop_npc(self):
        self.shop_npc_overlay = True
        if self.game_manager.current_shop_npc:
            npc = self.game_manager.current_shop_npc[0]
            self.refresh_shop_item(npc)

    def refresh_shop_item(self, npc: ShopNPC | None = None):
        items: list[dict]
        if npc and npc.shop_items:
            items = [random.choice(npc.shop_items)]
        elif self.game_manager.shop_items:
            items = [random.choice(self.game_manager.shop_items)]
        else:
            Logger.warning("[ShopNPC] No shop items available!")
            self.shop_npc_list.set_items([])
            return

        Logger.info(f"[ShopNPC] Refreshing shop items: {items}")
        self.shop_npc_list.set_items(items)
        self.current_npc_item = items[0] if items else None
        # Avoid refreshing every frame
        self.next_refresh_time = pg.time.get_ticks() + 5000

    def _get_shop_stock(self) -> list[dict]:
        """Default provider used by the generic shop overlay."""
        if not self.game_manager.shop_items:
            return []
        return [random.choice(self.game_manager.shop_items)]

    def close_shop_npc(self):
        self.shop_npc_overlay = False

    def _handle_npc_purchase(self) -> None:
        """Handle buy button for NPC shop."""
        item = self.current_npc_item
        if not item or item.get("count", 0) <= 0:
            return
        price = item.get("price", 0)
        bag_items = self.game_manager.bag.items if self.game_manager.bag else []
        if not self.game_manager.bag.spend_coins(price):
            Logger.warning("Not enough coins to buy")
            return
        # decrement NPC stock
        item["count"] = max(0, item.get("count", 0) - 1)
        # add to bag inventory
        for it in bag_items:
            if it.get("name") == item.get("name"):
                it["count"] += 1
                break
        else:
            bag_items.append({
                "name": item.get("name"),
                "count": 1,
                "sprite_path": item.get("sprite_path", "")
            })
        self._refresh_bag_items()
        if self.game_manager.current_shop_npc:
            current_npc = self.game_manager.current_shop_npc[0]
            self.shop_npc_list.set_items(current_npc.shop_items[:1])

    def save_game(self):
        """Save the current game state."""
        self.game_manager.save("saves/game0.json")
        Logger.info("Game saved successfully")

    def load_game(self):
        """Load the game state from file."""
        manager = GameManager.load("saves/game0.json")
        if manager is not None:
            self.game_manager = manager
            self._refresh_bag_items()
            Logger.info("Game loaded successfully")
        else:
            Logger.warning("Failed to load game")

        if self.game_manager.current_shop_npc:
            self.refresh_shop_item()

    def _refresh_bag_items(self):
        items = self.game_manager.bag.items if self.game_manager.bag else []
        monsters = self.game_manager.bag.monsters if self.game_manager.bag else []
        self.bag_item_list.set_items(items)
        self.bag_item_list.set_monsters(monsters)

    # Navigation Call
    def select_place(self, name):
        if name not in self.game_manager.places:
            Logger.warning(f"Unknown Place")
            return
        target = self.game_manager.places[name]
        player = self.game_manager.player
        if player is None:
            return
        start_tile = (int(player.position.x//GameSettings.TILE_SIZE),
                      int(player.position.y // GameSettings.TILE_SIZE))

        # Inside MAP navigation
        map_width = self.game_manager.current_map.tmxdata.width
        map_height = self.game_manager.current_map.tmxdata.height
        tx, ty = target
        if not (0 <= tx < map_width and 0 <= ty < map_height):
            Logger.warning("Target tile outside current map")
            return

        path = self.bfs_pathfind(start_tile, target)
        if not path:
            Logger.warning("No path")
            return
        self.navigation_path = path
        if len(self.navigation_path) > 0 and self.navigation_path[0] == start_tile:
            self.navigation_path.pop(0)
        self.is_navigating = True
        self.navigation_goal = target
        self.navigation_index = 0

    def bfs_pathfind(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]] | None:
        """Simple BFS pathfinding."""
        map_obj = self.game_manager.current_map
        map_w, map_h = map_obj.tmxdata.width, map_obj.tmxdata.height

        def walkable(x: int, y: int) -> bool:
            player = self.game_manager.player
            if player is None:
                return False

            w, h = player.animation.rect.size
            rect = pg.Rect(x * GameSettings.TILE_SIZE,
                           y * GameSettings.TILE_SIZE, w, h)

            # Block if enemy
            if self.game_manager.check_collision(rect):
                return False

            # Block if shopkeeper

            return True
        sx, sy = start
        gx, gy = goal
        if not (0 <= sx < map_w and 0 <= sy < map_h and 0 <= gx < map_w and 0 <= gy < map_h):
            return None

        queue = deque([start])
        came_from: dict[tuple[int, int],
                        tuple[int, int] | None] = {start: None}
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            cx, cy = cur
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < map_w and 0 <= ny < map_h and (nx, ny) not in came_from:
                    if walkable(nx, ny):
                        came_from[(nx, ny)] = cur
                        queue.append((nx, ny))

        if goal not in came_from:
            return None

        # reconstruct path
        path: list[tuple[int, int]] = []
        node = goal
        while node is not None:
            path.append(node)
            node = came_from[node]
        path.reverse()
        return path

    def _navigate_along_path(self, dt: float):
        """Move player along navigation_path using collision checks."""
        if not self.is_navigating or not self.navigation_path:
            self.is_navigating = False
            return

        player: Player = self.game_manager.player
        if player is None or self.navigation_goal is None:
            self.is_navigating = False
            return

        next_tile = self.navigation_path[0]
        target_x = next_tile[0] * GameSettings.TILE_SIZE
        target_y = next_tile[1] * GameSettings.TILE_SIZE

        dx = target_x - player.position.x
        dy = target_y - player.position.y
        dist = (dx**2 + dy**2) ** 0.5

        if dist == 0:
            self.navigation_path.pop(0)
            if not self.navigation_path:
                self.is_navigating = False
            return

        step = player.speed * dt
        move_x = dx if abs(dx) <= step else dx / dist * step
        move_y = dy if abs(dy) <= step else dy / dist * step

        # Move X
        rect_x = player.animation.rect.copy()
        rect_x.topleft = (player.position.x + move_x, player.position.y)
        if not self.game_manager.current_map.check_collision(rect_x):
            player.position.x += move_x
        else:
            player.position.x = player._snap_to_grid(player.position.x)

        # Move Y
        rect_y = player.animation.rect.copy()
        rect_y.topleft = (player.position.x, player.position.y + move_y)
        if not self.game_manager.current_map.check_collision(rect_y):
            player.position.y += move_y
        else:
            player.position.y = player._snap_to_grid(player.position.y)

        # Reached tile?
        if abs(player.position.x - target_x) < 1 and abs(player.position.y - target_y) < 1:
            player.position.x = target_x
            player.position.y = target_y
            self.navigation_path.pop(0)
            if not self.navigation_path:
                self.is_navigating = False

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()

    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()

    @override
    def update(self, dt: float):
        # Advance shop restock timers even when overlay closed (game time driven)
        self.game_manager.tick_shop(int(dt * 1000))
        self.shop_item_list.update(dt)

        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)

        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)

        for shop in self.game_manager.current_shop_npc:
            shop.update(dt)

            if shop.detected and input_manager.key_pressed(pg.K_SPACE):
                self.shop_overlay = False
                self.open_shop_npc()

        # Update bag
        self.game_manager.bag.update(dt)

        # Online manager update
        if self.game_manager.player and self.online_manager:
            player = self.game_manager.player
            dir_name = player.direction.name.lower()
            sprite_path = player.animation.path
            _ = self.online_manager.update(
                player.position.x,
                player.position.y,
                self.game_manager.current_map.path_name,
                direction=dir_name,
                sprite=sprite_path
            )
            self._update_remote_players(dt)

            import time
            if self.online_manager:
                try:
                    msgs = self.online_manager.get_recent_chat(50)
                    max_id = self._last_chat_id_seen
                    now = time.monotonic()
                    for m in msgs:
                        mid = int(m.get("id", 0))
                        if mid <= self._last_chat_id_seen:
                            continue
                        sender = int(m.get("from", -1))
                        text = str(m.get("text", ""))
                        if sender >= 0 and text:
                            self._chat_bubbles[sender] = (text, now + 5.0)
                        if mid > max_id:
                            max_id = mid
                    self._last_chat_id_seen = max_id
                except Exception:
                    pass

        if self.chat_overlay:
            if input_manager.key_pressed(pg.K_t):
                self.chat_overlay.open()
            self.chat_overlay.update(dt)

        # Get Player
        player = self.game_manager.player
        player.player_is_navigating = self.is_navigating
        # Teleport Check
        for tp in self.game_manager.current_map.teleporters:
            player_tile_x = int(player.position.x // GameSettings.TILE_SIZE)
            player_tile_y = int(player.position.y // GameSettings.TILE_SIZE)
            if player_tile_x == tp.pos.x and player_tile_y == tp.pos.y:
                # Perform teleport
                if not self.is_navigating:
                    self.game_manager.current_map = self.game_manager.maps[tp.destination]
                    player.position = tp.target_pos.copy()
                    player.rect.topleft = (tp.target_pos.x, tp.target_pos.y)
                    break  # only one teleport per update

        # Bush collision detection
        if self.game_manager.player is not None:
            player_rect = self.game_manager.player.rect  # Player must have rect
            self.player_in_bush = any(player_rect.colliderect(bush)
                                      for bush in self.bush_rects)

            if self.player_in_bush:
                if input_manager.key_pressed(pg.K_z) and not self.battle_triggered:
                    self.battle_triggered = True
                    capture_scene = scene_manager._scenes["capture_scene"]
                    capture_scene.set_game_manager(self.game_manager)
                    scene_manager.change_scene("capture_scene")
            else:
                self.battle_triggered = False

        # Update Settings Button and overlay
        self.settings_button.update(dt)
        if self.settings_overlay:
            self.back_button.update(dt)
            self.volume_slider.update(dt)
            self.mute_checkbox.update(dt)
            self.save_button.update(dt)
            self.load_button.update(dt)

        # Update Backpack Button and overlay
        self.backpack_button.update(dt)
        if self.backpack_overlay:
            self.back_button_backpack.update(dt)
            self.bag_item_list.update(dt)

        # Update Shop Button and overlay
        self.shop_button.update(dt)
        if self.shop_overlay:
            self.back_button_shop.update(dt)
            # refresh timer handled inside shop_item_list
            self.shop_item_list.update(dt)

        if self.shop_npc_overlay:
            self.shop_npc_list.update(dt)
            self.back_button_shop_npc.update(dt)
            self.buy_button_shop_npc.update(dt)

            if pg.time.get_ticks() >= self.next_refresh_time:
                self.refresh_shop_item()

        # Update Navigation Button
        self.place1_button.update(dt)
        self.place2_button.update(dt)
        self.place3_button.update(dt)

        # Navigating Movement
        if self.is_navigating:
            self._navigate_along_path(dt)

        # Apply pending map switches after everyone moves
        if not self.is_navigating:
            self.game_manager.try_switch_map()

    def _update_remote_players(self, dt: float) -> None:
        if not self.online_manager:
            return

        remote_list = self.online_manager.get_list_players()
        active_ids = set()

        for p in remote_list:

            pid = p.get("id")
            if pid is None:
                continue
            print(f"Remote data for pid={pid}: {p}")
            active_ids.add(pid)

            sprite_path = p.get("sprite", "character/ow1.png")
            info = self.remote_players.get(pid)
            if info is None or info.get("sprite") != sprite_path:
                anim = Animation(
                    sprite_path,
                    ["down", "left", "right", "up"],
                    4,
                    (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
                    loop=0.5
                )
                self.remote_players[pid] = {"anim": anim,
                                            "sprite": sprite_path,
                                            "data": p}
            else:
                self.remote_players[pid]["data"] = p

            anim: Animation = self.remote_players[pid]["anim"]

            # Step 2: update direction safely
            target_x = p.get("x", 0)
            target_y = p.get("y", 0)
            last_x, last_y = self._online_last_pos.get(
                pid, (target_x, target_y))

            dx = target_x - last_x
            dy = target_y - last_y

            # Tentukan arah
            if abs(dx) > abs(dy):
                dir_name = "right" if dx > 0 else "left"
            elif abs(dy) > 0:
                dir_name = "down" if dy > 0 else "up"
            else:
                dir_name = anim.cur_row  # tidak bergerak

            anim.switch(dir_name)

            # Step 1: smooth position update
            target_x = p.get("x", 0)
            target_y = p.get("y", 0)
            last_x, last_y = self._online_last_pos.get(
                pid, (target_x, target_y))
            lerp_speed = 8.0
            new_x = last_x + (target_x - last_x) * lerp_speed * dt
            new_y = last_y + (target_y - last_y) * lerp_speed * dt
            pos = Position(new_x, new_y)
            anim.update_pos(pos)
            self._online_last_pos[pid] = (new_x, new_y)

            # Step 3: only animate if moving
            is_moving = p.get("is_moving", True)
            if is_moving:
                anim.update(dt)

        # Remove stale entries (this is OUTSIDE the loop)
        for pid in list(self.remote_players.keys()):
            if pid not in active_ids:
                del self.remote_players[pid]
                self._online_last_pos.pop(pid, None)

    @override
    def draw(self, screen: pg.Surface):
        if self.game_manager.player:
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)

        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)

        # Draw Enemy Trainer
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        # Draw NPC Trainer
        for shop in self.game_manager.current_shop_npc:
            shop.draw(screen, camera)

        # Draw Minimap
        minimap_raw = self.game_manager.current_map.build_minimap()
        if minimap_raw:
            minimap_scaled = pg.transform.scale(minimap_raw, (150, 150))

            map_w = self.game_manager.current_map.tmxdata.width
            map_h = self.game_manager.current_map.tmxdata.height

            # player
            player = self.game_manager.player
            px_tile = player.position.x // GameSettings.TILE_SIZE
            py_tile = player.position.y // GameSettings.TILE_SIZE

            # scale tile coords → minimap coords
            px = int(px_tile * (150 / map_w))
            py = int(py_tile * (150 / map_h))

            # draw dot
            mm = minimap_scaled.copy()
            pg.draw.circle(mm, (255, 0, 0), (px, py), 3)

            # draw minimap
            minimap_x = screen.get_width() - 150 - 20
            minimap_y = 20
            screen.blit(mm, (minimap_x, minimap_y))

        self.game_manager.bag.draw(screen)

        if self.online_manager and self.game_manager.player:
            cam = self.game_manager.player.camera
            for pid, info in list(self.remote_players.items()):
                data = info.get("data")
                anim: Animation = info.get("anim")
                if not data or not anim:
                    continue
                if data.get("map") != self.game_manager.current_map.path_name:
                    continue
                anim.draw(screen, cam)

            try:
                self._draw_chat_bubbles(screen, cam)
            except Exception:
                pass

        if self.chat_overlay:
            self.chat_overlay.draw(screen)

        if self.game_manager.player:
            # Draw all bush rects in red
            # for bush in self.bush_rects:
            # rect_on_screen = camera.transform_rect(bush)
            # pg.draw.rect(screen, (255, 0, 0), rect_on_screen, 2)

            player_rect_on_screen = camera.transform_rect(
                self.game_manager.player.rect)
            pg.draw.rect(screen, (0, 255, 0), player_rect_on_screen, 2)

        # Settings Button
        self.settings_button.draw(screen)

        # Backpack Button
        self.backpack_button.draw(screen)

        # Shop Button
        self.shop_button.draw(screen)

        # Nav Button
        self.place1_button.draw(screen)
        self.place2_button.draw(screen)
        self.place3_button.draw(screen)

        # Debug NAV PATH
        if self.navigation_path:
            for tile in self.navigation_path:
                rect = pg.Rect(tile[0]*GameSettings.TILE_SIZE,
                               tile[1]*GameSettings.TILE_SIZE,
                               GameSettings.TILE_SIZE,
                               GameSettings.TILE_SIZE)
                rect = camera.transform_rect(rect)
                pg.draw.rect(screen, (0, 0, 255), rect, 2)

        # Draw overlay if backpack is active
        if self.backpack_overlay:
            # Darken background
            overlay = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))

            # Draw middle overlay panel
            pg.draw.rect(screen, (50, 50, 50),
                         self.backpack_rect)
            pg.draw.rect(screen, (200, 200, 200),
                         self.backpack_rect, 3)  # border

            # Draw overlay text
            font = pg.font.SysFont(None, 40)
            text = font.render("Backpack", True, (255, 255, 255))
            screen.blit(text, (self.backpack_rect.x + 30,
                        self.backpack_rect.y + 25))

            # Draw bag entries
            self.bag_item_list.draw(screen)

            # Draw back button
            self.back_button_backpack.draw(screen)

        # Draw Shop Overlay if active
        if self.shop_overlay:
            overlay = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))

            # Draw middle overlay panel
            pg.draw.rect(screen, (50, 50, 50),
                         self.overlay_rect)
            pg.draw.rect(screen, (200, 200, 200), self.overlay_rect,
                         3)  # border

            # Draw overlay text
            font = pg.font.SysFont(None, 30)
            text = font.render("Shop List", True, (255, 255, 255))
            screen.blit(text, (self.overlay_rect.x +
                        100, self.overlay_rect.y + 50))

            label_font = pg.font.SysFont(None, 24)

            self.back_button_shop.draw(screen)
            self.shop_item_list.draw(screen)

        # Draw SHOPNPC overlay if active
        if self.shop_npc_overlay:
            overlay = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))

            # Draw middle overlay panel
            pg.draw.rect(screen, (50, 50, 50),
                         self.overlay_rect)
            pg.draw.rect(screen, (200, 200, 200), self.overlay_rect,
                         3)  # border

            # Draw overlay text
            font = pg.font.SysFont(None, 30)
            text = font.render("Shop NPC List", True, (255, 255, 255))
            screen.blit(text, (self.overlay_rect.x +
                        100, self.overlay_rect.y + 50))

            label_font = pg.font.SysFont(None, 24)

            self.shop_npc_list.draw(screen)
            self.back_button_shop_npc.draw(screen)
            self.buy_button_shop_npc.draw(screen)

        # Draw overlay if active
        if self.settings_overlay:
            overlay = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))

            # Draw middle overlay panel
            pg.draw.rect(screen, (50, 50, 50),
                         self.overlay_rect)
            pg.draw.rect(screen, (200, 200, 200), self.overlay_rect,
                         3)  # border

            # Draw overlay text
            font = pg.font.SysFont(None, 30)
            text = font.render("Settings Menu", True, (255, 255, 255))
            screen.blit(text, (self.overlay_rect.x +
                        100, self.overlay_rect.y + 50))

            label_font = pg.font.SysFont(None, 24)
            # Draw volume label and percentage
            label_font = pg.font.SysFont(None, 24)
            volume_text = label_font.render("Volume", True, (255, 255, 255))
            screen.blit(volume_text, (self.volume_slider.x,
                                      self.volume_slider.y - 30))

            volume_percent = int(GameSettings.AUDIO_VOLUME * 100)
            percent_text = label_font.render(
                f"{volume_percent}%", True, (255, 255, 255))
            screen.blit(percent_text, (self.volume_slider.x +
                                       self.volume_slider.width - 50,
                                       self.volume_slider.y - 30))

            # Draw volume slider
            self.volume_slider.draw(screen)

            # Draw mute label
            mute_text = label_font.render("Mute Audio", True, (255, 255, 255))
            screen.blit(mute_text, (self.mute_checkbox.x +
                                    self.mute_checkbox.size + 10,
                                    self.mute_checkbox.y - 2))

            # Draw mute checkbox
            self.mute_checkbox.draw(screen)

            # Draw save and load buttons
            self.save_button.draw(screen)
            self.load_button.draw(screen)

            # Draw back button
            self.back_button.draw(screen)

    def _draw_chat_bubbles(self, screen: pg.Surface, cam: PositionCamera) -> None:
        if not self.online_manager:
            return

        import time
        now = time.monotonic()
        expired = [pid for pid,
                   (_, ts) in self._chat_bubbles.items() if ts <= now]
        for pid in expired:
            self._chat_bubbles.pop(pid, None)

        if not self._chat_bubbles:
            return

        local_pid = self.online_manager.player_id
        font = pg.font.SysFont("arial", 14)

        if self.game_manager.player and local_pid in self._chat_bubbles:
            text, _ = self._chat_bubbles[local_pid]
            self._draw_chat_bubble_for_pos(
                screen, cam, self.game_manager.player.position, text, font)

        for pid, (text, _) in self._chat_bubbles.items():
            if pid == local_pid:
                continue
            pos_xy = self._online_last_pos.get(pid)
            if not pos_xy:
                continue
            px, py = pos_xy
            self._draw_chat_bubble_for_pos(
                screen, cam, Position(px, py), text, font)

    def _draw_chat_bubble_for_pos(self, screen: pg.Surface, camera: PositionCamera, world_pos: Position, text: str, font: pg.font.Font):
        screen_pos = camera.transform_position(world_pos)
        sx, sy = screen_pos

        bubble_y = sy - GameSettings.TILE_SIZE - 20

        text_surf = font.render(text, True, (255, 255, 255))
        padding = 8
        bubble_w = text_surf.get_width() + padding * 2
        bubble_h = text_surf.get_height() + padding * 2

        bubble_x = sx - bubble_w // 2

        bg_surf = pg.Surface((bubble_w, bubble_h), pg.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        screen.blit(bg_surf, (bubble_x, bubble_y))

        screen.blit(text_surf, (bubble_x + padding, bubble_y + padding))

    def send_message(self, text: str) -> bool:
        """Send a chat message via online manager."""
        if self.online_manager:
            return self.online_manager.send_message(text)
        return False

    def get_messages(self, limit: int) -> list[dict]:
        """Get recent chat messages from online manager."""
        if self.online_manager:
            return self.online_manager.get_recent_chat(limit)
        return []
