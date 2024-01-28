from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

c = 4
h = 100
 

def ceil(n):
    return int(-1 * n // 1 * -1)


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
        self.blanks = self.calculate_blanks()

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
        self.post_rush_spaces = []

        self.should_rush_prev = False
        self.rebuilding = False

    
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
        self.bomber_arr = []
        for i in range(self.width):
            self.bomber_arr.append([])
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
                    self.bomber_arr.append(temp_count)
        bomber_list.sort(key = lambda x: x[0], reverse = True)
        return bomber_list
    
    def calculate_sniper(self):
        gunship_list = []
        self.sniper_arr = []
        for i in range(self.width):
            self.sniper_arr.append([])
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
                    self.sniper_arr.append(temp_count)
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
        for tile in self.map.tiles:
            if tile == Tile.ASTEROID:
                asteroids.append(tile)
        return asteroids
    
    def calculate_blanks(self):
        blanks = []
        for tile in self.map.tiles:
            if tile == Tile.SPACE:
                blanks.append(tile)
        return blanks
    # ---- init functions ---- #

    # ---- turn ---- #

    def play_turn(self, rc: RobotController):
        self.update_vals(rc)

        # try to rush:
        if len(self.map.path) <= 30 or self.opponent_rushing(rc) or self.hp == 2500 and self.enemy_hp < 2500 and enemy_hp < self.enemy_hp_last[-50]:
            self.rush(rc)
            self.towers_attack(rc)
            return

        # try to rush early while selling farms
        # if rc.get_towers(self.team) >= self.rush_const:
        #     self.sell_farms(rc)


        if (self.check_init_phase(rc)):
            self.initial_phase(rc)
        
        elif (self.rebuilding):
            self.rebuild()
        
        elif (self.should_rush(rc) == False and self.should_rush_prev == True):
            self.rebuilding = True
            self.rebuild()
       
        elif (len(self.bomber_list) == 0 and len(self.sniper_count) == 0):
            # board full
            if (self.should_rush(rc)):
                if (len(self.post_rush_spaces) == 0):
                    self.post_rush_spaces = self.sell_all_farms()
                self.rush(rc)

            # sell all farms
        else:
            # play as if safe
            if self.should_farm(rc):
                self.build_solar(rc)

            if (self.bomb_is_desirable() and len(self.bomber_list) > 0):
                self.build_bomber(rc)
            elif (len(self.sniper_list) > 0):
                self.build_sniper(rc)
            else:
                print("board should be full")

        self.towers_attack(rc)

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

    def rebuild(self, rc):
        if (len (self.post_rush_spaces) == 0):
            self.rebuilding = False
            return
        tile = self.post_rush_spaces[0]
        while len (self.post_rush_spaces) > 0:
            if (rc.can_build_tower(TowerType.SOLAR_FARM, tile[0], tile[1])):
                rc.build_tower(TowerType.SOLAR_FARM, tile[0], tile[1])
                if (len (self.post_rush_spaces) > 1):
                    tile = self.post_rush_spaces[1]
                self.post_rush_spaces.pop(0)
        
        if (len (self.post_rush_spaces) == 0):
            self.rebuilding = False

        
    def check_init_phase(self, rc):
        return (self.bomber_count == 0) or (self.hp == 2500 and self.solar_count < 10)
    
    def initial_phase(self, rc):
        if (self.bomber_count == 0):
            self.build_bomber(rc)
        else:
            self.build_solar(rc)
    
    def should_rush(self, rc):
        # if short path insta rush? 
        
        # 
        return
    
    def get_total_offensive(self):
        return self.bomber_count + self.sniper_count
    
    def bomb_is_desirable(self, rc):
        total = self.get_total_offensive()
        if (total == 0):
            return True
        
        #  check this logic
        return (self.bomber_count / total < 0.2 * len(self.path) / len(self.blanks))
    
    def debris_damage_needed(self, rc: RobotController):
        debris = rc.get_debris(rc.get_ally_team())
        hp = 0
        numballoons = 0
        for d in debris:
            hp = hp + d.health**2
            numballoons = numballoons + 1
        if (numballoons == 0):
            return 0
        hp = hp // numballoons
        return hp
    
    def is_safe(self, rc):
        avg = self.debris_damage_needed(rc) ** (1/2)
        return avg <= self.bomber_count * TowerType.BOMBER.damage * 5 + self.gunship_count * TowerType.GUNSHIP.damage * 3
    
    def should_farm(self, rc):
        self.is_safe() and self.get_total_offensive() > int(0.2 * self.solar_count)

    # ---- turn ---- #
            
    # ---- build functions ---- #
    
    def build_bomber(self, rc):
        if (len(self.bomber_list) < 1):
            return False
        
        top = self.bomber_list[0]
        while (not rc.is_placeable(self.team, top[1], top[2]) or top[0] == 0):
            self.bomber_list.pop(0)
            if (len(self.bomber_list) == 0):
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
            if (len(self.sniper_list) == 0):
                return False
            top = self.sniper_list[0]
        
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            density = rc.sense_towers_within_radius_squared(self.team, top[1], top[2], 5)
            sniper_density = [i for i in density if i.type == TowerType.GUNSHIP]
            reinforcer_density = [i for i in density if i.type == TowerType.REINFORCER]

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
        while (not rc.is_placeable(self.team, top[1], top[2]) or top[0] == 0):
            self.solar_list.pop(0)
            if (len(self.solar_list) < 1):
                return False
            top = self.solar_list[0]
        
        if (rc.can_build_tower(TowerType.SOLAR_FARM, top[1], top[2])):                

            density = rc.sense_towers_within_radius_squared(self.team, top[1], top[2], 5)
            solar_density = [i for i in density if i.type == TowerType.SOLAR_FARM]
            reinforcer_density = [i for i in density if i.type == TowerType.REINFORCER]

            if len(solar_density) >= 3 and len(reinforcer_density) == 0 and self.reinforcer_count * 6 < self.solar_count and self.solar_count >= 10:
                if rc.can_build_tower(TowerType.REINFORCER, top[1], top[2]):
                    rc.build_tower(TowerType.REINFORCER, top[1], top[2])
                    self.solar_list.pop(0)
                    self.reinforcer_count += 1 
            else:
                self.solar_list.pop(0)
                rc.build_tower(TowerType.SOLAR_FARM, top[1], top[2])
                self.solar_count += 1
                return True



    # ---- build functions ---- #

    # ---- attack functions ---- #

    def towers_attack(self, rc):
        towers = rc.get_towers(self.team)

        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    # ---- attack functions ---- #

    # ---- rushing ---- #

    def rush(self, rc):
        i = 0
        c = 4
        h = 101 

        while rc.can_send_debris(c, h) and i < 2 * self.enemy_hp:
            rc.send_debris(c,h)
            i += 1

    def opponent_rushing(self, rc):
        debris = rc.get_debris(self.team)

        return len([d for d in debris if d.sent_by_opponent]) > 0

    def compute_damage(self, rc, cooldown):
        dmg = 0 

        for tower in rc.get_towers(self.enemy_team):
            bombTiles = self.bomber_arr[tower.x][tower.y]
            sniperTiles = self.sniper_arr[tower.x][tower.y]

            if tower.type == TowerType.BOMBER:
                dmg += 6 * ceil(bombTiles * cooldown / 15)
            elif tower.type == TowerType.GUNSHIP:
                dmg += 25 * ceil(sniperTiles * cooldown / 20) / 2
    

    def sell_all_farms(self, rc):
        towers = rc.get_towers(rc.get_ally_team())
        temp = []
        for tower in towers:
            temp.append(tower)

        spaces = []
        
        for tower in temp:
            if (tower.type == TowerType.SOLAR_FARM):
                x = tower.x 
                y = tower.y
                rc.sell_tower(tower.id)
                print(self.distances[x][y])
                if (self.distances[x][y] < 8):
                    rc.build_tower(TowerType.GUNSHIP, x, y) 
                    self.gunship_count += 1  
                else:
                    spaces.append([x, y])

            elif (tower.type == TowerType.REINFORCER):
                x = tower.x 
                y = tower.y
                if (self.distances[x][y] >= 8):
                    rc.sell_tower(tower.id)   
                    spaces.append([x, y])    

        self.pure_income = 10
        return spaces