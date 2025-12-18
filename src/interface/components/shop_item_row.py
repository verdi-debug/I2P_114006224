import pygame as pg
from src.core.services import input_manager, resource_manager
from src.interface.components.component import UIComponent


class ShopItemRow(UIComponent):
    """Single row for shop display. Supports optional buying via `clickable_buy` flag."""

    def __init__(self, x: int, y: int, width: int, height: int, clickable_buy: bool = False):
        self.rect = pg.Rect(x, y, width, height)
        self.padding = 10
        self.hover = False

        # icon/text
        self.icon_size = 36
        self.icon_surface = None
        self.name_surface = None

        # price
        self.price = 0
        self.price_font = pg.font.SysFont("arial", 20)
        self.price_surface = None

        # buy area/button
        self.clickable_buy = clickable_buy
        self.buy_label_surface = pg.font.SysFont(
            "arial", 18).render("BUY", True, (255, 255, 255))
        self.buy_rect = None  # computed in draw
        self.on_buy = None

        self.name_font = pg.font.SysFont("arial", 22)

        # item data
        self.count = 1
        self.mode = "item"

    def set_position(self, x: int, y: int) -> None:
        self.rect.topleft = (x, y)

    def set_item(self, icon_path: str, name: str, price: int, count: int = 1) -> None:
        # set item visuals + price
        if icon_path:
            base = resource_manager.get_image(icon_path)
            self.icon_surface = pg.transform.scale(
                base, (self.icon_size, self.icon_size))
        else:
            self.icon_surface = pg.Surface(
                (self.icon_size, self.icon_size), pg.SRCALPHA)

        self.name_surface = self.name_font.render(
            name or "-", True, (255, 255, 255))
        self.price = price or 0
        self.price_surface = self.price_font.render(
            f"{self.price}G", True, (220, 220, 0))
        self.count = count
        self.item_data = {"sprite_path": icon_path, "name": name,
                          "price": price, "count": count}

    def set_buy_handler(self, cb) -> None:
        self.on_buy = cb

    def update(self, dt: float) -> None:
        del dt
        self.hover = self.rect.collidepoint(input_manager.mouse_pos)
        if (self.clickable_buy and self.buy_rect and
                self.buy_rect.collidepoint(input_manager.mouse_pos) and
                input_manager.mouse_pressed(1) and self.on_buy):
            self.on_buy(self.item_data)

    def draw(self, screen: pg.Surface) -> None:
        bg = (60, 60, 60) if self.hover else (35, 35, 35)
        pg.draw.rect(screen, bg, self.rect, border_radius=6)

        if not self.icon_surface or not self.name_surface:
            return

        # icon
        icon = pg.transform.scale(
            self.icon_surface, (self.icon_size, self.icon_size))
        icon_y = self.rect.y + (self.rect.height - icon.get_height()) // 2
        screen.blit(icon, (self.rect.x + self.padding, icon_y))

        text_x = self.rect.x + self.padding + icon.get_width() + 10
        screen.blit(self.name_surface, (text_x, self.rect.y + 8))

        # price on right
        price_x = self.rect.right - self.padding - self.price_surface.get_width()
        screen.blit(self.price_surface, (price_x, self.rect.y + 8))

        # buy area
        if self.clickable_buy:
            buy_w = 58
            buy_h = 28
            buy_x = self.rect.right - self.padding - buy_w
            buy_y = self.rect.bottom - self.padding - buy_h
            self.buy_rect = pg.Rect(buy_x, buy_y, buy_w, buy_h)
            pg.draw.rect(screen, (90, 130, 70) if self.buy_rect.collidepoint(input_manager.mouse_pos) else (70, 100, 50),
                         self.buy_rect, border_radius=6)
            # center label
            label_rect = self.buy_label_surface.get_rect(
                center=self.buy_rect.center)
            screen.blit(self.buy_label_surface, label_rect)
        else:
            self.buy_rect = None
