import pygame as pg
from src.utils.settings import GameSettings
from src.scenes.scene import Scene
from src.sprites import BackgroundSprite
from src.utils.definition import Monster
from src.core.services import scene_manager
from typing import override
from src.core import GameManager
from src.interface.components import Button


class BattleScene(Scene):
    game_manager: GameManager | None
    enemy_trainer: "EnemyTrainer | None"
    player_monster: Monster | None
    enemy_monster: Monster | None
    turn_state: str
    timer: float
    background: BackgroundSprite
    attack_button: Button
    run_button: Button
    strength_buff: int
    defense_buff: int

    def __init__(self):
        super().__init__()
        self.game_manager = None
        self.enemy_trainer = None
        self.player_monster = None
        self.enemy_monster = None
        self.strength_buff = 0
        self.defense_buff = 0
        self.turn_state = "player_turn"
        self.timer = 0

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        self.background = BackgroundSprite("backgrounds/background1.png")

        # Attack Button
        self.attack_button = Button(
            "UI/button_play.png", "UI/button_play_hover.png",
            px + 50, py, 100, 100,
            self.player_attack
        )

        # Run Button
        self.run_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px - 100, py, 100, 100,
            lambda: scene_manager.change_scene("game")
        )

        # Heal Button
        self.heal_button = Button(
            "UI/button_heal (1).png", "UI/button_heal (1).png",
            px - 600, py - 350, 100, 100,
            self.player_heal
        )

        # Strengh Potion
        self.strength_button = Button(
            "UI/button_strength (1).png", "UI/button_strength (1).png",
            px - 600, py - 250, 100, 100,
            self.use_strength_potion
        )

        # Defense Potion
        self.defense_button = Button(
            "UI/button_defense (1).png", "UI/button_defense (1).png",
            px - 600, py - 150, 100, 100,
            self.use_defense_potion
        )

    # Callback for attack button

    def player_attack(self):
        if self.turn_state == "player_turn":
            self.turn_state = "player_attack_animation"
            self.timer = 1.0
            self.attack_button.enabled = False
            self.run_button.enabled = False
            self.heal_button.enabled = False
            self.strength_button.enabled = False
            self.defense_button.enabled = False

    def player_heal(self):
        if self.turn_state != "player_turn":
            return
        if not self.consume_item("Heal Potion"):
            return

        self.player_monster["hp"] += 20
        if self.player_monster["hp"] > self.player_monster["max_hp"]:
            self.player_monster["hp"] = self.player_monster["max_hp"]

        self.turn_state = "enemy_attack_animation"
        self.timer = 1.0

        self.attack_button.enabled = False
        self.run_button.enabled = False
        self.heal_button.enabled = False
        self.strength_button.enabled = False
        self.defense_button.enabled = False

    def use_strength_potion(self):
        if self.turn_state != "player_turn":
            return
        if not self.consume_item("Attack Potion"):
            return

        self.strength_buff += 20
        self.turn_state = "enemy_attack_animation"
        self.timer = 1.0

        self.attack_button.enabled = True
        self.run_button.enabled = True
        self.heal_button.enabled = self.get_item_count("Heal Potion") > 0
        self.strength_button.enabled = self.get_item_count("Attack Potion") > 0
        self.defense_button.enabled = self.get_item_count("Defense Potion") > 0

    def use_defense_potion(self):
        if self.turn_state != "player_turn":
            return
        if not self.consume_item("Defense Potion"):
            return

        self.turn_state = "enemy_attack_animation"
        self.timer = 1.0

        self.defense_buff += 15  # reduce next enemy attack by 15
        # Keep turn state same, just enable buttons
        self.attack_button.enabled = True
        self.run_button.enabled = True
        self.heal_button.enabled = self.get_item_count("Heal Potion") > 0
        self.strength_button.enabled = self.get_item_count("Attack Potion") > 0
        self.defense_button.enabled = self.get_item_count("Defense Potion") > 0

    def get_item_count(self, item_name: str) -> int:
        for item in self.game_manager.bag.items:
            if item["name"] == item_name:
                return item["count"]
        return 0

    def consume_item(self, item_name: str, amount: int = 1) -> bool:
        for item in self.game_manager.bag.items:
            if item["name"] == item_name and item["count"] >= amount:
                item["count"] -= amount
                return True
        return False

    @override
    def set_game_manager(self, game_manager: GameManager) -> None:
        self.game_manager = game_manager
        monster = game_manager.bag.monsters[0]
        name_to_sprite = {
            "Pikachu": "assets/images/menu_sprites/menusprite1.png",
            "Charizard": "assets/images/menu_sprites/menusprite2.png",
            "Blastoise": "assets/images/menu_sprites/menusprite3.png",
            "Venusaur": "assets/images/menu_sprites/menusprite4.png",
            "Gengar": "assets/images/menu_sprites/menusprite5.png",
            "Dragonite": "assets/images/menu_sprites/menusprite6.png",
        }
        sprite_path = name_to_sprite[monster["name"]]

        self.player_monster = {
            "name": monster["name"],
            "hp": monster["hp"],
            "max_hp": monster["max_hp"],
            "level": monster["level"],
            "sprite_path": sprite_path,
            "sprite": pg.image.load(sprite_path).convert_alpha()
        }

    @override
    def set_enemy_trainer(self, enemy_trainer: "EnemyTrainer") -> None:
        self.enemy_trainer = enemy_trainer
        monster = enemy_trainer.monsters[0]
        name_to_sprite = {
            "Pikachu": "assets/images/menu_sprites/menusprite1.png",
            "Charizard": "assets/images/menu_sprites/menusprite2.png",
            "Blastoise": "assets/images/menu_sprites/menusprite3.png",
            "Venusaur": "assets/images/menu_sprites/menusprite4.png",
            "Gengar": "assets/images/menu_sprites/menusprite5.png",
            "Dragonite": "assets/images/menu_sprites/menusprite6.png",
        }
        sprite_path = name_to_sprite[monster["name"]]

        self.enemy_monster = {
            "name": monster["name"],
            "hp": monster["hp"],
            "max_hp": monster["max_hp"],
            "level": monster["level"],
            "sprite_path": sprite_path,
            "sprite": pg.image.load(sprite_path).convert_alpha()
        }

        self.turn_state = "player_turn"
        self.timer = 0
        self.strength_buff = 0
        self.defense_buff = 0

        self.attack_button.enabled = True
        self.run_button.enabled = True

    @override
    def update(self, dt: float) -> None:
        self.attack_button.update(dt)
        self.run_button.update(dt)
        self.heal_button.update(dt)
        self.strength_button.update(dt)
        self.defense_button.update(dt)

        if self.turn_state == "player_attack_animation":
            self.timer -= dt
            if self.timer <= 0:
                damage = 30 + self.strength_buff
                self.enemy_monster["hp"] -= damage
                self.strength_buff = 0
                if self.enemy_monster["hp"] <= 0:
                    self.enemy_monster["hp"] = 0
                    self.game_manager.bag.add_coins(10)
                    self.turn_state = "end"
                else:
                    self.turn_state = "enemy_attack_animation"
                    self.timer = 1.0

        elif self.turn_state == "enemy_attack_animation":
            self.timer -= dt
            if self.timer <= 0:
                damage = 20 - self.defense_buff
                if damage < 0:
                    damage = 0
                self.player_monster["hp"] -= damage
                self.defense_buff = 0
                if self.player_monster["hp"] <= 0:
                    self.player_monster["hp"] = 0
                    self.turn_state = "end"
                else:
                    self.turn_state = "player_turn"
                    self.attack_button.enabled = True
                    self.run_button.enabled = True
                    self.heal_button.enabled = self.get_item_count(
                        "Heal Potion") > 0
                    self.strength_button.enabled = self.get_item_count(
                        "Attack Potion") > 0
                    self.defense_button.enabled = self.get_item_count(
                        "Defense Potion") > 0

        elif self.turn_state == "end":
            self.run_button.enabled = True
            self.attack_button.enabled = True
            self.heal_button.enabled = self.get_item_count("Heal Potion") > 0
            self.strength_button.enabled = self.get_item_count(
                "Attack Potion") > 0
            self.defense_button.enabled = self.get_item_count(
                "Defense Potion") > 0

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.attack_button.draw(screen)
        self.run_button.draw(screen)
        self.heal_button.draw(screen)
        self.strength_button.draw(screen)
        self.defense_button.draw(screen)

        font = pg.font.SysFont(None, 30)

        # Player Monster
        player_sprite = self.player_monster["sprite"]
        player_pos = (150, GameSettings.SCREEN_HEIGHT // 2)

        if self.player_monster["hp"] > 0:
            screen.blit(player_sprite, player_pos)
        else:
            fainted_text = font.render("DEAD", True, (255, 0, 0))
            screen.blit(fainted_text, player_pos)

        # Player Monster HP
        player_hp_text = font.render(
            f'HP: {self.player_monster["hp"]}/{self.player_monster["max_hp"]}',
            True, (255, 255, 255)
        )
        screen.blit(player_hp_text, (player_pos[0], player_pos[1] - 40))

        # Enemy Monster
        enemy_sprite = self.enemy_monster["sprite"]
        enemy_pos = (GameSettings.SCREEN_WIDTH - 150,
                     GameSettings.SCREEN_HEIGHT // 2)
        if self.enemy_monster["hp"] > 0:
            screen.blit(enemy_sprite, enemy_pos)
        else:
            fainted_text = font.render("DEAD", True, (255, 0, 0))
            screen.blit(fainted_text, enemy_pos)

        # Enemy monster HP above monster
        enemy_hp_text = font.render(
            f'HP: {self.enemy_monster["hp"]}/{self.enemy_monster["max_hp"]}',
            True, (255, 255, 255)
        )
        screen.blit(enemy_hp_text, (enemy_pos[0], enemy_pos[1] - 40))
