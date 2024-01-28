from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

class BotPlayer(Player):
    def get_unique_idx(self, i, j):
        return i * self.map_width + j
    
    def get_coords_from_idx(self, idx):
        return (int(idx / self.map_width), idx % self.map_width)

    def parse_map(self):
        for i in range(0, self.map_width):
            # print(i)
            for j in range (0, self.map_height):
                # print(j)
                tile = self.map.tiles[i][j]

                # idx = self.get_unique_idx(i, j)

                if (tile == Tile.PATH):
                    self.path_list += [[i, j]]

                elif (tile == Tile.SPACE):
                    self.space_list += [[i, j]]

                else:
                    self.block_list += [[i, j]]
                # print(self.space_list)
    
    def calculate_distance(self, tile1, tile2):
        return (tile1[0] - tile2[0])**2 + (tile1[1] - tile2[1])**2

    def calculate_ranges(self):
        for tile in self.space_list:
            idx = self.get_unique_idx(tile[0], tile[1])
            self.gunship_ranges[idx] = []
            self.bomber_ranges[idx] = []

            for path in self.path_list:
                if (self.calculate_distance(tile, path) < TowerType.GUNSHIP.range):
                    self.gunship_ranges[idx] += [path]
                
                if (self.calculate_distance(tile, path) < TowerType.BOMBER.range):
                    self.bomber_ranges[idx] += [path]

    def __init__(self, map: Map):
        self.map = map

        self.team = None
        # self.balance = 0
        self.map_height = self.map.height
        self.map_width = self.map.width

        self.path_list = []
        self.space_list = []
        self.block_list = []

        # self.map_arr = []
        # for i in range(self.map_width):
        #     self.map_arr.append([])
        #     for j in range(self.map_height):
        #         if (i, j) in self.path_list:
        #             self.map_arr.append(1)
        #         else:
        #             self.map_arr.append(0)

        self.gunship_ranges = {}
        self.bomber_ranges = {}

        # get path, space, block list
        self.parse_map()
        self.calculate_ranges()

        print(self.gunship_ranges)
    

    def play_turn(self, rc: RobotController):
        # some sort of state machine here
        self.team = rc.get_ally_team()
        self.balance = rc.get_balance(self.team)
        debris = rc.get_debris(self.team)
        # print(debris)


        for i in debris:
            print(i)