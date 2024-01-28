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

        # print(self.gunship_ranges)
    
    def calculate_optimal_bomber(self, bomber):
        if (bomber[2] > 1):
            return 0
        if (bomber[2] == 0):
            return bomber[1]
        return bomber[1] / 2
    
    def calculate_optimal_gs(self, gs):
        if (gs[2] == 0):
            return gs[1]
        return gs[1] / gs[2]

    def get_b_list(self, rc, debris):
        b_list = []
        for bomber in self.bomber_ranges:
            temp = self.get_coords_from_idx(bomber)
            if (not rc.is_placeable(self.team, temp[0], temp[1])):
                continue

            for i in debris:
                x_coord = i.x
                y_coord = i.y
                if ([x_coord, y_coord] in self.bomber_ranges[bomber]):
                    # towers = rc.sense_towers_within_radius_squared(self.team, x_coord, y_coord, TowerType.BOMBER.range)
                    total = 0
                    for tower in rc.get_towers(self.team):
                        if (tower.type == TowerType.BOMBER) and self.calculate_distance([tower.x, tower.y], temp) <= TowerType.BOMBER.range:
                            total += 1
                    b_list += [[bomber, len(self.bomber_ranges[bomber]), total]]
        return b_list

    def get_gs_list(self, rc, debris):
        gs_list = []
        for gunship in self.gunship_ranges:
            temp = self.get_coords_from_idx(gunship)
            if (not rc.is_placeable(self.team, temp[0], temp[1])):
                continue

            for i in debris:
                x_coord = i.x
                y_coord = i.y
                if ([x_coord, y_coord] in self.gunship_ranges[gunship]):
                    # towers = rc.sense_towers_within_radius_squared(self.team, x_coord, y_coord, TowerType.BOMBER.range)
                    total = 0
                    for tower in rc.get_towers(self.team):
                        if (tower.type == TowerType.GUNSHIP) and self.calculate_distance([tower.x, tower.y], temp) <= TowerType.GUNSHIP.range:
                            total += 1
                    gs_list += [[gunship, len(self.gunship_ranges[gunship]), total]]
        return gs_list

    def play_turn(self, rc: RobotController):
        # print(rc.get_time_remaining_at_start_of_turn(self.team))
        # some sort of state machine here
        self.team = rc.get_ally_team()
        self.balance = rc.get_balance(self.team)
        debris = rc.get_debris(self.team)

        b_list = self.get_b_list(rc, debris)
        gs_list = self.get_gs_list(rc, debris)

        
        optimal_b = None
        if(len(b_list) > 0):
            optimal_b = b_list[0]
            max_weight = 0
            for i in range(len(b_list)):
                desired = self.get_coords_from_idx(b_list[i][0])
                if (rc.can_build_tower(TowerType.BOMBER, desired[0], desired[1])):
                    weight = self.calculate_optimal_bomber(b_list[i])
                    if (weight > max_weight):
                        max_weight = weight
                        optimal_b = b_list[i]

        optimal_gs = None
        if(len(gs_list) > 0):
            # print(gs_list)
            optimal_gs = gs_list[0]
            max_weight = 0
            for i in range(len(gs_list)):
                desired = self.get_coords_from_idx(gs_list[i][0])
                if (rc.can_build_tower(TowerType.GUNSHIP, desired[0], desired[1])):
                    weight = self.calculate_optimal_bomber(gs_list[i])
                    if (weight > max_weight):
                        max_weight = weight
                        optimal_gs = gs_list[i]

        num_b = 0
        num_gs = 0
        for tower in rc.get_towers(self.team):
            if (tower.type == TowerType.BOMBER):
                num_b += 1
            elif (tower.type == TowerType.GUNSHIP):
                num_gs += 1

        if (len(rc.get_debris(self.team)) >= 10):
            if (num_b <= num_gs and optimal_b != None):
                desired = self.get_coords_from_idx(optimal_b[0])
                if (rc.can_build_tower(TowerType.BOMBER, desired[0], desired[1])):
                    print("BUILDING BOMBER")
                    rc.build_tower(TowerType.BOMBER, desired[0], desired[1])

            elif (num_gs < num_b and optimal_gs != None):
                desired = self.get_coords_from_idx(optimal_gs[0])
                if (rc.can_build_tower(TowerType.GUNSHIP, desired[0], desired[1])):
                    print("BUILDING GUNSHIP")
                    rc.build_tower(TowerType.GUNSHIP, desired[0], desired[1])
        
        # else:
        #     desired = self.get_coords_from_idx(optimal_gs[0])
        #     if (rc.can_build_tower(TowerType.GUNSHIP, desired[0], desired[1])):
        #         print("BUILDING GUNSHIP")
        #         rc.build_tower(TowerType.GUNSHIP, desired[0], desired[1])
        
        # elif self.balance > TowerType.REINFORCER.cost * 5:
        #     max_towers = 0
        #     optimal = [0, 0]
        #     for tile in self.space_list:
        #         if rc.can_build_tower(TowerType.REINFORCER, tile[0], tile[1]):
        #             num_towers = 0
        #             for tower in rc.get_towers(self.team):
        #                 if (self.calculate_distance([tower.x, tower.y], tile) <= TowerType.REINFORCER.range):
        #                     num_towers += 1
        #             if (num_towers > max_towers):
        #                 max_towers = num_towers
        #                 optimal = tile
            
        #     if (rc.can_build_tower(TowerType.REINFORCER, optimal[0], optimal[1])):
        #         print("BUILDING REINFORCER")
        #         rc.build_tower(TowerType.REINFORCER, optimal[0], optimal[1])
        
        else:
            min_impact = self.map_width*self.map_height
            optimal = [0, 0]
            for tile in self.gunship_ranges:
                fixed = self.get_coords_from_idx(tile)
                # print(fixed)
                if rc.can_build_tower(TowerType.SOLAR_FARM, fixed[0], fixed[1]):
                    if len(self.gunship_ranges[tile]) < min_impact:
                        min_impact = len(self.gunship_ranges[tile])
                        optimal = fixed

            # print(optimal)
            if rc.can_build_tower(TowerType.SOLAR_FARM, optimal[0], optimal[1]):
                print("BUILDING SOLAR FARM")
                rc.build_tower(TowerType.SOLAR_FARM, optimal[0], optimal[1])            

        for tower in rc.get_towers(self.team):
            if (tower.type == TowerType.BOMBER):
                rc.auto_bomb(tower.id)
            elif (tower.type == TowerType.GUNSHIP):
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
