import pygame
import math
from MapData import HexMap, HexTile

# === 기본 설정 ===
pygame.init()
screen = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("Hex Map Viewer")
clock = pygame.time.Clock()

# === 상수 설정 ===
HEX_SIZE = 40
WIDTH = math.sqrt(3) * HEX_SIZE
HEIGHT = 2 * HEX_SIZE
HORIZ_SPACING = WIDTH
VERT_SPACING = HEIGHT * 3/4

# === 헥스 타일의 중심 좌표 계산 함수 ===
def hex_to_pixel(q, r):
    x = WIDTH * (q + r/2)
    y = VERT_SPACING * r
    return (int(x), int(y))

# === 헥스 타일을 그리는 함수 ===
def draw_hexagon(surface, color, position):
    x, y = position
    points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)
        px = x + HEX_SIZE * math.cos(angle_rad)
        py = y + HEX_SIZE * math.sin(angle_rad)
        points.append((px, py))
    pygame.draw.polygon(surface, color, points, 2)

# === 마우스 위치에 해당하는 타일 찾기 ===
def find_tile_at_pixel(x, y, hex_map, offset_x, offset_y):
    for tile in hex_map.tiles.values():
        center_x, center_y = hex_to_pixel(tile.q, tile.r)
        center_x += offset_x
        center_y += offset_y
        dist = math.hypot(center_x - x, center_y - y)
        if dist < HEX_SIZE * 0.9:
            return tile
    return None

# === 맵 데이터 (미국 스타일)
usa_hex_map = {
    (0, 0): "AK",
    (0, 2): "WA", (1, 2): "MT", (2, 2): "ND", (3, 2): "MN", (4, 2): "WI",
    (0, 3): "ID", (1, 3): "WY", (2, 3): "SD", (3, 3): "IA", (4, 3): "IL",
    (-1, 4): "OR", (0, 4): "NV", (1, 4): "CO", (2, 4): "NE", (3, 4): "MO",
    (-1, 5): "CA", (0, 5): "AZ", (1, 5): "UT", (2, 5): "KS", (3, 5): "AR",
    (0, 6): "NM", (1, 6): "OK", (2, 6): "LA",
    (0, 7): "TX",
    (5, 3): "IN", (6, 3): "OH", (7, 3): "PA", (8, 3): "NJ", (9, 3): "CT",
    (4, 4): "KY", (5, 4): "WV", (6, 4): "MD", (7, 4): "DE",
    (4, 5): "TN", (5, 5): "VA", (6, 5): "NC",
    (3, 6): "MS", (4, 6): "AL", (5, 6): "SC",
    (4, 7): "GA",
    (4, 8): "FL",
    (6, 2): "MI",
    (8, 2): "NY", (9, 2): "MA", (10, 2): "RI",
    (9, 1): "VT", (10, 1): "NH",
    (11, 0): "ME",
    (8, 4): "DC"
}

# === 맵 생성
hex_map = HexMap()
for (q, r), region_name in usa_hex_map.items():
    s = -q - r
    tile = HexTile(q, r, s, region_name=region_name, country_name="United States", population=1000)
    hex_map.tiles[(q, r, s)] = tile

# === 오프셋 및 드래그 초기화 ===
offset_x = 600
offset_y = 400
dragging = False
drag_start = (0, 0)
camera_start = (0, 0)

# === 메인 루프 ===
running = True
while running:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                drag_start = pygame.mouse.get_pos()
                camera_start = (offset_x, offset_y)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                mx, my = pygame.mouse.get_pos()
                dx = mx - drag_start[0]
                dy = my - drag_start[1]
                offset_x = camera_start[0] + dx
                offset_y = camera_start[1] + dy

    mouse_x, mouse_y = pygame.mouse.get_pos()
    hovered_tile = find_tile_at_pixel(mouse_x, mouse_y, hex_map, offset_x, offset_y)

    for tile in hex_map.tiles.values():
        pos = hex_to_pixel(tile.q, tile.r)
        center_x = pos[0] + offset_x
        center_y = pos[1] + offset_y

        draw_hexagon(screen, (0, 0, 0), (center_x, center_y))

        font_small = pygame.font.SysFont(None, 16)
        font_large = pygame.font.SysFont(None, 20)

        coord_text = font_small.render(f"({tile.q},{tile.r})", True, (0, 0, 0))
        screen.blit(coord_text, (center_x - coord_text.get_width() // 2, center_y - 20))

        region_text = font_large.render(tile.region_name, True, (0, 0, 0))
        screen.blit(region_text, (center_x - region_text.get_width() // 2, center_y + 5))

    if hovered_tile:
        info_font = pygame.font.SysFont(None, 24)
        info_lines = [
            f"Region: {hovered_tile.region_name}",
            f"Country: {hovered_tile.country_name}",
            f"Population: {hovered_tile.population}",
            f"Infection Rate: {hovered_tile.infection_rate:.2%}",
            f"Resources: {hovered_tile.resources}"
        ]
        for idx, line in enumerate(info_lines):
            text = info_font.render(line, True, (0, 0, 0))
            screen.blit(text, (10, 10 + idx * 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()