class HexTile:
    def __init__(self, q, r, s, region_name="", country_name="", population=0):
        self.q = q
        self.r = r
        self.s = s
        
        self.region_name = region_name  # 지역명 (서울, 경기도 등)
        self.country_name = country_name  # 국가명 (대한민국, 미국 등)

        self.population = population  # 인구
        self.infection_rate = 0.0  # 감염률 (0.0 ~ 1.0)
        self.resources = 0  # 자원량

        self.neighbors = []  # [(neighbor_tile, direction_index)]
        self.borders = [False for _ in range(6)]  # 육각형 6변마다 방어선 여부

    def add_neighbor(self, neighbor_tile, direction_index):
        self.neighbors.append((neighbor_tile, direction_index))

    def build_wall(self, edge_index):
        self.borders[edge_index] = True

    def has_wall(self, edge_index):
        return self.borders[edge_index]

    def __repr__(self):
        return f"HexTile({self.region_name}, Pop: {self.population})"

class HexMap:
    def __init__(self):
        self.tiles = {}  # (q, r, s) -> HexTile

    def find_tile_by_region(self, region_name):
        for tile in self.tiles.values():
            if tile.region_name == region_name:
                return tile
        return None

    def get_tiles_by_country(self, country_name):
        return [tile for tile in self.tiles.values() if tile.country_name == country_name]
