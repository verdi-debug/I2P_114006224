import pygame as pg
import random
from src.utils.settings import GameSettings
from src.scenes.scene import Scene
from src.sprites import BackgroundSprite
from src.utils.definition import Monster
from src.core.services import scene_manager
from typing import override
from src.core import GameManager
from src.interface.components import Button

# monster list
WILD_MONSTER_TEMPLATES = {
    "Pikachu": {"sprite_path": "menu_sprites/menusprite1.png", "base_hp": 80, "base_level": 5},
    "Charizard": {"sprite_path": "menu_sprites/menusprite2.png", "base_hp": 150, "base_level": 10},
    "Blastoise": {"sprite_path": "menu_sprites/menusprite3.png", "base_hp": 140, "base_level": 10},
    "Venusaur": {"sprite_path": "menu_sprites/menusprite4.png", "base_hp": 145, "base_level": 10},
    "Gengar": {"sprite_path": "menu_sprites/menusprite5.png", "base_hp": 90, "base_level": 8},
    "Dragonite": {"sprite_path": "menu_sprites/menusprite6.png", "base_hp": 160, "base_level": 15},
}


class CaptureScene(Scene):
    game_manager: GameManager | None
    player_monster: Monster | None
    enemy_monster: Monster | None
    turn_state: str
    timer: float
    background: BackgroundSprite
    attack_button: Button
    capture_button: Button
    run_button: Button
    player_sprite: pg.Surface | None
    enemy_sprite: pg.Surface | None

    def __init__(self):
        super().__init__()
        self.game_manager = None
        self.player_monster = None
        self.enemy_monster = None
        self.turn_state = "player_turn"
        self.timer = 0
        self.capture_attempt_text = ""
        self.player_sprite = None
        self.enemy_sprite = None

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        self.background = BackgroundSprite("backgrounds/background1.png")

        # Attack Button
        self.attack_button = Button(
            "UI/button_play.png", "UI/button_play_hover.png",
            px - 150, py, 100, 100,
            self.monster_attack,
        )

        # Capture Button
        self.capture_button = Button(
            "UI/button_shop.png", "UI/button_shop_hover.png",
            px, py, 100, 100,
            self.monster_capture,
        )

        # Run Button
        self.run_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px + 150, py, 100, 100,
            lambda: scene_manager.change_scene("game"),
        )

    def _create_monster(self, name: str) -> Monster:
        template = WILD_MONSTER_TEMPLATES[name]
        sprite_path = template["sprite_path"]
        hp = template["base_hp"]
        level = template["base_level"]

        return {
            "name": name,
            "hp": hp,
            "max_hp": hp,
            "level": level,
            "sprite_path": sprite_path
        }

    def _set_wild_monster(self) -> None:
        monster_name = random.choice(list(WILD_MONSTER_TEMPLATES.keys()))
        self.enemy_monster = self._create_monster(monster_name)

        self.enemy_sprite = pg.image.load(
            f"assets/images/{self.enemy_monster['sprite_path']}").convert_alpha()
        print(f"A wild {monster_name} appeared!")

    def monster_attack(self):
        if self.turn_state == "player_turn":
            self.turn_state = "player_attack_animation"
            self.timer = 1.0
            self.capture_attempt_text = f"{self.player_monster['name']} attacked!"
            self.attack_button.enabled = False
            self.capture_button.enabled = False
            self.run_button.enabled = False

    def monster_capture(self):
        if self.turn_state == "player_turn":
            max_hp = self.enemy_monster["max_hp"]
            current_hp = self.enemy_monster["hp"]

            capture_multiplier = max(
                0.1, min(1.0, 1.0 - (current_hp / max_hp) * 0.9))
            capture_chance = 25 * capture_multiplier

            if random.random() * 100 < capture_chance:
                self.capture_attempt_text = f"Success! {self.enemy_monster['name']} was captured!"

                captured_monster = {
                    "name": self.enemy_monster["name"],
                    "hp": self.enemy_monster["hp"],
                    "max_hp": self.enemy_monster["max_hp"],
                    "level": self.enemy_monster["level"],
                    "sprite_path": self.enemy_monster["sprite_path"]
                }
                self.game_manager.bag.monsters.append(captured_monster)
                self.turn_state = "end_capture"
            else:
                self.capture_attempt_text = f"Aww! {self.enemy_monster['name']} broke free!"
                self.turn_state = "enemy_attack_animation"

            self.attack_button.enabled = False
            self.capture_button.enabled = False
            self.run_button.enabled = False
            self.timer = 1.0

    @override
    def set_game_manager(self, game_manager: GameManager) -> None:
        self.game_manager = game_manager

        player_monster_data = game_manager.bag.monsters[0]

        self.player_monster = {
            "name": player_monster_data["name"],
            "hp": player_monster_data["hp"],
            "max_hp": player_monster_data["max_hp"],
            "level": player_monster_data["level"],
            "sprite_path": player_monster_data["sprite_path"]
        }

        self.player_sprite = pg.image.load(
            f"assets/images/{self.player_monster['sprite_path']}").convert_alpha()

    @override
    def enter(self) -> None:
        if self.game_manager is not None:
            self._set_wild_monster()
            self.turn_state = "player_turn"
            self.timer = 0
            self.capture_attempt_text = f"A wild {self.enemy_monster['name']} appeared!"

            self.attack_button.enabled = True
            self.capture_button.enabled = True
            self.run_button.enabled = True

    @override
    def update(self, dt: float) -> None:
        self.attack_button.update(dt)
        self.capture_button.update(dt)
        self.run_button.update(dt)

        if self.turn_state == "player_attack_animation":
            self.timer -= dt
            if self.timer <= 0:
                self.enemy_monster["hp"] -= 30
                if self.enemy_monster["hp"] <= 0:
                    self.enemy_monster["hp"] = 0
                    self.turn_state = "end_defeat"
                    self.game_manager.bag.add_coins(5)
                    self.capture_attempt_text = f"The wild {self.enemy_monster['name']} died!"
                    self.timer = 2.0
                else:
                    self.turn_state = "enemy_attack_animation"
                    self.timer = 1.0

        elif self.turn_state == "enemy_attack_animation":
            self.timer -= dt
            if self.timer <= 0:
                self.player_monster["hp"] -= 20

                if self.player_monster["hp"] <= 0:
                    self.player_monster["hp"] = 0
                    self.turn_state = "end_defeat"
                    self.capture_attempt_text = f"{self.player_monster['name']} died! You lost the battle."
                    self.timer = 2.0
                else:
                    self.turn_state = "player_turn"
                    self.attack_button.enabled = True
                    self.capture_button.enabled = True
                    self.run_button.enabled = True
                    self.capture_attempt_text = "What will you do?"

        elif self.turn_state in ["end_defeat", "end_capture"]:
            self.timer -= dt
            if self.timer <= 0:
                if self.game_manager:
                    self.game_manager.bag.monsters[0]["hp"] = self.player_monster["hp"]
                scene_manager.change_scene("game")

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.attack_button.draw(screen)
        self.capture_button.draw(screen)
        self.run_button.draw(screen)

        font = pg.font.SysFont(None, 30)

        # Player Monster
        player_pos = (150, GameSettings.SCREEN_HEIGHT // 2)

        if self.player_monster["hp"] > 0:
            screen.blit(self.player_sprite, player_pos)
        else:
            fainted_text = font.render("DEAD", True, (255, 0, 0))
            screen.blit(fainted_text, player_pos)

        # Player Monster HP
        player_hp_text = font.render(
            f'HP: {self.player_monster["hp"]}/{self.player_monster["max_hp"]} - LVL {self.player_monster["level"]}',
            True, (255, 255, 255)
        )
        screen.blit(player_hp_text, (player_pos[0], player_pos[1] - 40))

        # Enemy Monster
        enemy_pos = (GameSettings.SCREEN_WIDTH - 150 - self.enemy_sprite.get_width(),
                     GameSettings.SCREEN_HEIGHT // 2)

        if self.enemy_monster["hp"] > 0:
            screen.blit(self.enemy_sprite, enemy_pos)
        else:
            fainted_text = font.render("DEAD", True, (255, 0, 0))
            screen.blit(fainted_text, enemy_pos)

        enemy_hp_text = font.render(
            f'HP: {self.enemy_monster["hp"]}/{self.enemy_monster["max_hp"]} - LVL {self.enemy_monster["level"]}',
            True, (255, 255, 255)
        )
        screen.blit(enemy_hp_text, (enemy_pos[0] + 50, enemy_pos[1] - 40))

        status_text = font.render(
            self.capture_attempt_text, True, (255, 255, 255)
        )

        status_pos = (
            GameSettings.SCREEN_WIDTH // 2 - status_text.get_width() // 2,
            GameSettings.SCREEN_HEIGHT - 50
        )
        screen.blit(status_text, status_pos)
