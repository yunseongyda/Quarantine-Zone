import pygame
import sys
import random
import math

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
FPS = 30
HEX_RADIUS = 40  # hexagon radius in pixels
RESOURCE_START = 200
FACTORY_COST = 50
LAB_COST = 100
WALL_COST = 20  # cost to build a wall
MAX_LABS = 2
RESEARCH_RATE = 1  # research progress per tick per lab
RESEARCH_TARGET = 100  # percent needed for victory
MAP_RADIUS = 5  # hex grid radius

# Directions for hex neighbors in cube coords
DIRECTIONS = [
    (1, -1, 0), (1, 0, -1), (0, 1, -1),
    (-1, 1, 0), (-1, 0, 1), (0, -1, 1)
]

class Tile:
    def __init__(self, q, r, s):
        self.q, self.r, self.s = q, r, s
        self.survivors = random.randint(50, 150)
        self.infected = 0
        self.resource_amount = random.randint(50, 150)
        self.building = None  # 'factory', 'lab'
        self.walls = [False] * 6  # wall on each hex side
        self.neighbors = []  # list of (neighbor_tile, direction_index)

    @property
    def infection_rate(self):
        total = self.survivors + self.infected
        return (self.infected / total) if total > 0 else 0

class Grid:
    def __init__(self, radius):
        self.radius = radius
        self.tiles = {}
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r
                if abs(s) <= radius:
                    self.tiles[(q, r, s)] = Tile(q, r, s)
        # link neighbors
        for tile in self.tiles.values():
            for i, d in enumerate(DIRECTIONS):
                nb = self.tiles.get((tile.q + d[0], tile.r + d[1], tile.s + d[2]))
                if nb:
                    tile.neighbors.append((nb, i))
        # start infection
        start = random.choice(list(self.tiles.values()))
        start.infected = 1

    def pixel_from_cube(self, q, r):
        x = HEX_RADIUS * math.sqrt(3) * (q + r / 2)
        y = HEX_RADIUS * 1.5 * r
        return x, y

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hex Infection Strategy")
        self.clock = pygame.time.Clock()
        self.grid = Grid(MAP_RADIUS)
        self.state = 'MENU'
        self.resources = RESOURCE_START
        self.labs_count = 0
        self.research_progress = 0
        self.camera_offset = pygame.Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        self.dragging = False
        self.font = pygame.font.Font(None, 18)
        self.overlay_mode = 0  # 0=off,1=infection,2=resources,3=population
        self.build_mode = 'factory'  # 'factory','lab','wall'
        # precompute hex corners
        self.hex_corners = [
            (HEX_RADIUS * math.cos(math.radians(60*i+30)),
             HEX_RADIUS * math.sin(math.radians(60*i+30)))
            for i in range(6)
        ]

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if self.state == 'MENU':
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.state = 'PLAYING'
            elif self.state == 'PLAYING':
                if e.type == pygame.KEYDOWN:
                    # overlay toggles
                    if e.key == pygame.K_1: self.overlay_mode = 1
                    elif e.key == pygame.K_2: self.overlay_mode = 2
                    elif e.key == pygame.K_3: self.overlay_mode = 3
                    elif e.key == pygame.K_0: self.overlay_mode = 0
                    # build mode toggles
                    elif e.key == pygame.K_f: self.build_mode = 'factory'
                    elif e.key == pygame.K_l: self.build_mode = 'lab'
                    elif e.key == pygame.K_w: self.build_mode = 'wall'
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1: self.build_action(e.pos)
                    elif e.button == 3:
                        self.dragging = True
                        self.drag_start = pygame.Vector2(e.pos)
                        self.cam_start = self.camera_offset.copy()
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 3:
                    self.dragging = False
                elif e.type == pygame.MOUSEMOTION and self.dragging:
                    mv = pygame.Vector2(e.pos)
                    self.camera_offset = self.cam_start + (mv - self.drag_start)

    def build_action(self, pos):
        mouse = pygame.Vector2(pos) - self.camera_offset
        for tile in self.grid.tiles.values():
            x, y = self.grid.pixel_from_cube(tile.q, tile.r)
            center = pygame.Vector2(x, y)
            if (mouse - center).length() < HEX_RADIUS:
                # build wall mode: determine side by angle
                if self.build_mode == 'wall' and self.resources >= WALL_COST:
                    rel = mouse - center
                    angle = math.degrees(math.atan2(rel.y, rel.x)) + 360 + 30
                    idx = int(angle // 60) % 6
                    if not tile.walls[idx]:
                        tile.walls[idx] = True
                        self.resources -= WALL_COST
                # build lab
                elif self.build_mode == 'lab' and tile.building is None and self.labs_count < MAX_LABS and self.resources >= LAB_COST:
                    tile.building = 'lab'
                    self.labs_count += 1
                    self.resources -= LAB_COST
                # build factory
                elif self.build_mode == 'factory' and tile.building is None and self.resources >= FACTORY_COST:
                    tile.building = 'factory'
                    self.resources -= FACTORY_COST
                return

    def update(self):
        if self.state == 'PLAYING':
            self.spread_infection()
            self.process_production()
            self.check_end()

    def spread_infection(self):
        new_inf = []
        for tile in self.grid.tiles.values():
            rate = tile.infection_rate
            if 0 < rate < 1:
                for nb, idx in tile.neighbors:
                    if not tile.walls[idx] and nb.infection_rate < 1 and random.random() < rate * 0.05:
                        new_inf.append(nb)
        for t in new_inf:
            if t.survivors > 0: t.survivors -= 1
            t.infected += 1

    def process_production(self):
        for tile in self.grid.tiles.values():
            if tile.building == 'factory':
                if tile.resource_amount > 0:
                    tile.resource_amount -= 1; self.resources += 1
                else: tile.building = None
            elif tile.building == 'lab':
                self.research_progress += RESEARCH_RATE
        if self.research_progress >= RESEARCH_TARGET:
            self.state = 'VICTORY'

    def check_end(self):
        if all(t.infection_rate >= 1 for t in self.grid.tiles.values()):
            self.state = 'GAME_OVER'

    def draw(self):
        self.screen.fill((30, 30, 30))
        if self.state == 'MENU':
            txt = self.font.render("Click to Start", True, (200, 200, 200))
            rect = txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(txt, rect)
        else:
            for tile in self.grid.tiles.values():
                x, y = self.grid.pixel_from_cube(tile.q, tile.r)
                pos = pygame.Vector2(x, y) + self.camera_offset
                pts = [(pos.x+cx, pos.y+cy) for cx, cy in self.hex_corners]
                pygame.draw.polygon(self.screen, (100, 100, 100), pts, 1)
                # draw walls
                for i, wall in enumerate(tile.walls):
                    if wall:
                        c1 = pts[i]
                        c2 = pts[(i+1)%6]
                        pygame.draw.line(self.screen, (0,0,0), c1, c2, 4)
                # infection overlay
                rate = tile.infection_rate
                if rate > 0:
                    alpha = min(200, int(200 * rate))
                    surf = pygame.Surface((HEX_RADIUS*2, HEX_RADIUS*2), pygame.SRCALPHA)
                    poly = [(HEX_RADIUS+cx, HEX_RADIUS+cy) for cx, cy in self.hex_corners]
                    pygame.draw.polygon(surf, (255, 0, 0, alpha), poly)
                    self.screen.blit(surf, (pos.x-HEX_RADIUS, pos.y-HEX_RADIUS))
                # buildings
                if tile.building == 'factory':
                    pygame.draw.circle(self.screen, (180, 180, 0), pos, HEX_RADIUS/3)
                elif tile.building == 'lab':
                    pygame.draw.circle(self.screen, (0, 0, 255), pos, HEX_RADIUS/3)
                # overlays
                txt_label = None
                if self.overlay_mode == 1:
                    txt_label = f"{tile.infection_rate*100:.0f}%"
                elif self.overlay_mode == 2:
                    txt_label = f"R:{tile.resource_amount}"
                elif self.overlay_mode == 3:
                    txt_label = f"S:{tile.survivors}/I:{tile.infected}"
                if txt_label:
                    label = self.font.render(txt_label, True, (255, 255, 255))
                    rect = label.get_rect(center=pos)
                    self.screen.blit(label, rect)
            # UI
            pygame.draw.rect(self.screen, (50, 50, 50), (10, 10, 280, 140))
            self.screen.blit(self.font.render(f"Resources: {self.resources}", True, (255, 255, 255)), (20, 20))
            self.screen.blit(self.font.render(f"Labs: {self.labs_count}/{MAX_LABS}", True, (255, 255, 255)), (20, 45))
            pygame.draw.rect(self.screen, (100, 100, 250), (20, 70, 200, 10), 1)
            w = min(200, self.research_progress/RESEARCH_TARGET*200)
            pygame.draw.rect(self.screen, (100, 100, 250), (20, 70, w, 10))
            info = f"Overlay:{self.overlay_mode} Mode:{self.build_mode.capitalize()} (F/L/W)"
            self.screen.blit(self.font.render(info, True, (255, 255, 255)), (20, 95))
            if self.state == 'VICTORY':
                msg = self.font.render("Victory! Vaccine Completed!", True, (0, 255, 0))
                self.screen.blit(msg, (SCREEN_WIDTH//2-100, 20))
            elif self.state == 'GAME_OVER':
                msg = self.font.render("Game Over. All Tiles Infected.", True, (255, 0, 0))
                self.screen.blit(msg, (SCREEN_WIDTH//2-120, 20))
        pygame.display.flip()

if __name__ == '__main__':
    Game().run()
