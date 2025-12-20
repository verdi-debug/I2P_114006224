import pygame as pg
from src.core.services import input_manager
from src.interface.components.component import UIComponent
from src.interface.components.shop_item_row import ShopItemRow


class ShopItemList(UIComponent):

    def __init__(self, x: int, y: int, width: int, height: int, clickable_buy: bool = False):
        self.rect = pg.Rect(x, y, width, height)
        self.row_height = 58
        self.row_gap = 6
        self.scroll_step = 24
        self.clickable_buy = clickable_buy

        self.rows: list[ShopItemRow] = []
        self.scroll = 0
        self.max_scroll = 0

        self.get_shop_items = lambda: []
        self.on_buy = None

        self.empty_font = pg.font.SysFont("arial", 20)
        self.font = pg.font.SysFont("arial", 14)

    def set_provider(self, fn):
        self.get_shop_items = fn

    def set_on_buy(self, fn):
        self.on_buy = fn

    def set_items(self, items: list[dict]) -> None:
        self.rows = []
        local_y = 0

        # Limit the number of items to 1 (Pokéball in this case)
        for entry in items[:1]:  # Only take the first item (Pokéball)
            row = ShopItemRow(self.rect.x, 0, self.rect.width,
                              self.row_height, clickable_buy=self.clickable_buy)
            row.set_item(entry.get("sprite_path", ""), entry.get(
                "name", "Unknown"), entry.get("price", 0), entry.get("count", 0))

            if self.clickable_buy and self.on_buy:
                row.set_buy_handler(lambda e=entry: self.on_buy(e))

            row._local_y = local_y
            self.rows.append(row)
            local_y += self.row_height + self.row_gap

        self.scroll = 0
        self._clamp_scroll()

    def force_refresh(self):
        data = self.get_shop_items()
        self.set_items(data)

    def _clamp_scroll(self):
        total = len(self.rows) * (self.row_height +
                                  self.row_gap) - self.row_gap
        visible = self.rect.height
        self.max_scroll = max(0, total - visible)
        self.scroll = max(0, min(self.scroll, self.max_scroll))

    def update(self, dt: float) -> None:
        if self.rows and self.rect.collidepoint(input_manager.mouse_pos):
            wheel = input_manager.mouse_wheel
            if wheel != 0:
                self.scroll -= wheel * self.scroll_step
                self._clamp_scroll()

        for row in self.rows:
            row_y = self.rect.y + row._local_y - self.scroll
            row.set_position(self.rect.x, row_y)
            if row.rect.bottom < self.rect.y or row.rect.y > self.rect.bottom:
                continue
            row.update(dt)

    def draw(self, screen: pg.Surface) -> None:
        pg.draw.rect(screen, (25, 25, 25), self.rect, border_radius=8)
        pg.draw.rect(screen, (180, 180, 180), self.rect, 2, border_radius=8)

        if not self.rows:
            message = self.empty_font.render(
                "No stock", True, (220, 220, 220))
            screen.blit(message, message.get_rect(center=self.rect.center))
            return

        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        for row in self.rows:
            if row.rect.bottom < self.rect.y or row.rect.y > self.rect.bottom:
                continue
            row.draw(screen)
        screen.set_clip(old_clip)
