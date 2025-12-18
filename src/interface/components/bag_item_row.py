import pygame as pg

from src.core.services import input_manager, resource_manager
from src.interface.components.component import UIComponent


class BagItemRow(UIComponent):
    """A tiny helper widget that shows one item line inside the bag overlay."""

    def __init__(self, x: int, y: int, width: int, height: int):
        # Container
        self.rect = pg.Rect(x, y, width, height)
        self.padding = 10
        self.hover = False

        # Item mode
        self.icon_size = 36
        self.icon_surface = None
        self.name_surface = None
        self.count_surface = None

        self.name_font = pg.font.SysFont("arial", 22)
        self.count_font = pg.font.SysFont("arial", 18)

        # Monster mode
        self.monster_icon_size = 36
        self.monster_icon_surface = None
        self.monster_name_surface = None
        self.monster_count_surface = None

        self.monster_name_font = pg.font.SysFont("arial", 22)
        self.monster_count_font = pg.font.SysFont("arial", 18)

        # Default mode
        self.mode = "item"

    def set_position(self, x: int, y: int) -> None:
        self.rect.topleft = (x, y)

    def set_item(self, icon_path: str, name: str, count: int) -> None:
        self.mode = "item"

        if icon_path:
            base = resource_manager.get_image(icon_path)
            self.icon_surface = pg.transform.scale(
                base, (self.icon_size, self.icon_size))
        else:
            self.icon_surface = pg.Surface(
                (self.icon_size, self.icon_size), pg.SRCALPHA)

        self.name_surface = self.name_font.render(
            name or "-", True, (255, 255, 255))
        self.count_surface = self.count_font.render(
            f"x{count}", True, (210, 210, 210))

    def set_monsters(self, monster_path: str, name: str, count: int) -> None:
        self.mode = "monster"

        if monster_path:
            base = resource_manager.get_image(monster_path)
            self.monster_icon_surface = pg.transform.scale(
                base, (self.monster_icon_size, self.monster_icon_size)
            )
        else:
            self.monster_icon_surface = pg.Surface(
                (self.monster_icon_size, self.monster_icon_size), pg.SRCALPHA
            )

        self.monster_name_surface = self.monster_name_font.render(
            name or "-", True, (255, 255, 255))
        self.monster_count_surface = self.monster_count_font.render(
            f"x{count}", True, (210, 210, 210))

    def update(self, dt: float) -> None:
        del dt
        self.hover = self.rect.collidepoint(input_manager.mouse_pos)

    def draw(self, screen: pg.Surface) -> None:
        icon_boost = 6 if self.hover else 0
        bg = (60, 60, 60) if self.hover else (35, 35, 35)

        # Background box
        pg.draw.rect(screen, bg, self.rect, border_radius=6)

        if self.mode == "item":
            if not self.icon_surface or not self.name_surface:
                return

            icon = pg.transform.scale(
                self.icon_surface,
                (self.icon_size + icon_boost, self.icon_size + icon_boost),
            )

            icon_y = self.rect.y + (self.rect.height - icon.get_height()) // 2
            screen.blit(icon, (self.rect.x + self.padding, icon_y))

            text_x = self.rect.x + self.padding + icon.get_width() + 10

            # Name
            screen.blit(self.name_surface, (text_x, self.rect.y + 8))

            # Count
            if self.count_surface:
                screen.blit(
                    self.count_surface,
                    (text_x, self.rect.bottom - self.count_surface.get_height() - 8),
                )
            return

        if self.mode == "monster":
            if (self.monster_icon_surface is None or
                self.monster_name_surface is None or
                    self.monster_count_surface is None):
                return

            monster = pg.transform.scale(
                self.monster_icon_surface,
                (self.monster_icon_size + icon_boost,
                 self.monster_icon_size + icon_boost),
            )

            monster_y = self.rect.y + \
                (self.rect.height - monster.get_height()) // 2
            screen.blit(monster, (self.rect.x + self.padding, monster_y))

            text_x = self.rect.x + self.padding + monster.get_width() + 10

            screen.blit(self.monster_name_surface, (text_x, self.rect.y + 8))
            screen.blit(
                self.monster_count_surface,
                (text_x, self.rect.bottom -
                 self.monster_count_surface.get_height() - 8),
            )
