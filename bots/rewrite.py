from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

c = 4
h = 100



class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.height = map.height
        self.width = map.width
        self.path = map.path

        self.distances = self.calculate_distance()
        self.bomber_list = self.calculate_bomber()
        self.sniper_list = self.calculate_sniper()
        self.solar_list = self.calculate_solar()
        self.asteroids = self.calculate_asteroids()

        self.bomber_count = 0
        self.sniper_count = 0
        self.solar_count = 0
        self.reinforcer_count = 0

        self.team = None
        self.enemy_team = None

        self.enemy_hp = 2500
        self.enemy_hp_prev = [2500] * 51
        self.hp = 2500
        self.hp_prev = [2500] * 51

        self.prev_wealth = 1500
        self.curr_wealth = self.prev_wealth
        self.pure_income = 10

    
    # ---- init functions ---- #
    def calculate_distance(self):
        distances = []
        for i in range (self.width):
            temp = []
            for j in range (self.height):
                min = 100000
                for (x, y) in self.path:
                    new = (i - x)**2 + abs(j - y)**2
                    if (new < min):
                        min = new
                temp.append(min)
            distances.append(temp)
        return distances
    
    def calculate_bomber(self):
        bomber_list = []
        for i in range(self.width):
            for j in range(self.height):
                if self.map.is_space(i, j):
                    temp_count = 0
                    for k in range(7):
                        for l in range(7):
                            new_x = i - 3 + k
                            new_y = j - 3 + k
                            if (new_x - i)**2 + (new_y - j)**2 < 10:
                                if (self.map.is_path(new_x, new_y)):
                                    temp_count += 1
                    bomber_list.append((temp_count, i, j))
        bomber_list.sort(key = lambda x: x[0], reverse = True)
        return bomber_list
    
    def calculate_sniper(self):
        gunship_list = []
        for i in range(self.width):
            for j in range(self.height):
                if self.map.is_space(i, j):
                    temp_count = 0
                    for k in range(15):
                        for l in range(15):
                            new_x = i - 7 + k
                            new_y = j - 7 + k
                            if (new_x - i)**2 + (new_y - j)**2 < 60:
                                if (self.map.is_path(new_x, new_y)):
                                    temp_count += 1
                    gunship_list.append((temp_count, i, j))
        gunship_list.sort(key = lambda x: x[0], reverse = True)
        return gunship_list
    
    def calculate_solar(self):
        solar_list = []
        for i in range(self.width):
            for j in range(self.height):
                if self.map.is_space(i, j):
                    temp_count = 0
                    for k in range(15):
                        for l in range(15):
                            new_x = i - 7 + k
                            new_y = j - 7 + k
                            if (new_x - i)**2 + (new_y - j)**2 < 60:
                                if (self.map.is_path(new_x, new_y)):
                                    temp_count += 1
                    solar_list.append((temp_count, i, j))
        solar_list.sort(key = lambda x: x[0], reverse = False)
        return solar_list

    def calculate_asteroids(self):
        asteroids = []
        for tile in self.map:
            if map.is_asteroid(tile.x, tile.y):
                asteroids.append(tile)
        return asteroids
    # ---- init functions ---- #

    # ---- turn ---- #

    def play_turn(self, rc: RobotController):
        self.update_vals(rc)

        if (self.check_init_phase(rc)):
            self.initial_phase()
        elif (len(self.bomber_list) == 0 and len(self.sniper_count) == 0)
            # board full

    def update_vals(self, rc):
        if self.team == None:
            self.team = rc.get_ally_team()
        if self.enemy_team == None:
            self.enemy_team = rc.get_enemy_team()
        
        
        self.prev_wealth = self.curr_wealth
        self.curr_wealth = rc.get_balance(self.team)

        self.hp_prev.append(self.hp)
        self.enemy_hp_prev.append(self.enemy_hp)

        self.hp = rc.get_health(self.team)
        self.enemy_hp = rc.get_health(self.enemy_team)

        
    def check_init_phase(self, rc):
        return (self.bomber_count == 0) or (self.hp == 2500 and self.solar_count < 10)
    
    def initial_phase(self, rc):
        if (self.bomber_count == 0):
            self.build_bomber(rc)
        else:
            self.build_solar(rc)

    # ---- turn ---- #
            
    # ---- build functions ---- #
    
    def build_bomber(self, rc):
        if (len(self.bomber_list) < 1):
            return False
        
        top = self.bomber_list[0]
        while (not rc.is_placeable(self.team, top[1], top[2]) or top[0] == 0):
            self.bomber_list.pop(0)
            if (len(self.bomber_list) < 1):
                return False
            top = self.bomber_list[0]
        
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.bomber_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])
            self.bomber_count += 1
            return True
        
        return False
    
    def build_sniper(self, rc):
        if (len(self.sniper_list) < 1):
            return False
        
        top = self.sniper_list[0]
        while (not rc.is_placeable(self.team, top[1], top[2]) or top[0] == 0):
            self.sniper_list.pop(0)
            if (len(self.sniper_list) < 1):
                return False
            top = self.sniper_list[0]
        
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            density = rc.sense_towers_within_radius_squared(self.team, top[1], top[2], 5)
            sniper_density = [item for item in density if item.type == TowerType.GUNSHIP]
            reinforcer_density = [item for item in density if item.type == TowerType.REINFORCER]

            if len(sniper_density) >= 3 and (len(reinforcer_density) == 0) and (self.reinforcer_count * 6 < self.sniper_count):
                if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
                    self.sniper_list.pop(0)
                    rc.build_tower(TowerType.GUNSHIP, top[1], top[2])
                    self.sniper_count += 1
                    return True
            else:
                self.sniper_list.pop(0)
                rc.build_tower(TowerType.GUNSHIP, top[1], top[2])
                self.sniper_count += 1
        
        return False
    
    def build_solar(self, rc):
        top = self.solar_list[0]
        
        top = self.solar_list[0]
        while (not rc.is_placeable(self.team, top[1], top[2]) or top[0] == 0):
            self.solar_list.pop(0)
            if (len(self.solar_list) < 1):
                return False
            top = self.solar_list[0]
        
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.solar_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])
            self.solar_count += 1
            return True