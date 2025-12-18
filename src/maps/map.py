import pygame as pg
import pytmx
from src.entities.enemy_trainer import EnemyTrainer

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport


class Map:
    # Map Properties
    path_name: str
    tmxdata: pytmx.TiledMap
    # Position Argument
    spawn: Position
    teleporters: list[Teleport]
    # Rendering Properties
    _surface: pg.Surface
    _collision_map: list[pg.Rect]

    def __init__(self, path: str, tp: list[Teleport], spawn: Position):
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp

        pixel_w = self.tmxdata.width * GameSettings.TILE_SIZE
        pixel_h = self.tmxdata.height * GameSettings.TILE_SIZE

        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        self._collision_map = self._create_collision_map()

    def build_minimap(self):
        map_w = self.tmxdata.width
        map_h = self.tmxdata.height

        mini = pg.Surface((map_w, map_h))
        default_color = (0, 0, 0)  # fallback if no property

        # Fill initially
        mini.fill(default_color)

        # Get all visible tile layers
        layers = [layer for layer in self.tmxdata.visible_layers
                  if isinstance(layer, pytmx.TiledTileLayer)]

        for y in range(map_h):
            for x in range(map_w):
                rgb_color = default_color

                # Go from topmost layer down
                for layer in reversed(layers):
                    gid = layer.data[y][x]
                    if gid != 0:
                        # Check if the layer has a minimap_color property
                        if "minimap_color" in layer.properties:
                            color = layer.properties["minimap_color"]
                            r = int(color[3:5], 16)
                            g = int(color[5:7], 16)
                            b = int(color[7:9], 16)
                            rgb_color = (r, g, b)
                        else:
                            color = default_color
                        break  # stop at the first visible tile

                mini.set_at((x, y), rgb_color)

        return mini

    def update(self, dt: float):
        return

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))

        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0),
                             camera.transform_rect(rect), 1)

    def check_collision(self, rect: pg.Rect) -> bool:
        for collision_rect in self._collision_map:
            if rect.colliderect(collision_rect):
                return True
        return False

    def _render_all_layers(self, target: pg.Surface) -> None:
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)

    def _render_tile_layer(self, target: pg.Surface, layer: pytmx.TiledTileLayer) -> None:
        for x, y, gid in layer:
            if gid == 0:
                continue
            image = self.tmxdata.get_tile_image_by_gid(gid)
            if image is None:
                continue

            image = pg.transform.scale(
                image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            target.blit(image, (x * GameSettings.TILE_SIZE,
                        y * GameSettings.TILE_SIZE))

    def _create_collision_map(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("collision" in layer.name.lower() or "house" in layer.name.lower()):
                for x, y, gid in layer:
                    if gid != 0:
                        rect = pg.Rect(
                            x * GameSettings.TILE_SIZE,
                            y * GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE
                        )
                        rects.append(rect)
        return rects

    def check_teleport(self, player_rect: pg.Rect) -> Teleport | None:
        for tp in self.teleporters:
            # <-- use Teleport method for correct rect
            if tp.collides_with(player_rect):
                return tp
        return None

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        tp = [Teleport.from_dict(t) for t in data["teleport"]]
        pos = Position(data["player"]["x"] * GameSettings.TILE_SIZE,
                       data["player"]["y"] * GameSettings.TILE_SIZE)
        return cls(data["path"], tp, pos)

    def to_dict(self):
        return {
            "path": self.path_name,
            "teleport": [t.to_dict() for t in self.teleporters],
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            }
        }
