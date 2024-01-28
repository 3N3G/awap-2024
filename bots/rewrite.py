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

        self.rushing = False

        print(self.blanks)

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
        self.post_rush_spaces = []

        self.should_rush_prev = False
        self.rebuilding = False
        self.rushing = False

    
    # ---- init functions ---- #
    def calculate_distance(self):
        distances = []
        for i in range(self.width):
            distances.append([])
            for j in range(self.height):
                curmin = 10000
                for (x,y) in self.map.path:
                    curmin = min((abs(i-x)**2 + abs(j-y)**2)**(1/2), curmin) 
                distances[i].append(curmin)
        return distances

    
    def calculate_bomber(self):
        bomber_list = []
        for i in range(self.width):
            for j in range(self.height):
                if self.map.is_space(i, j):
                    tmpCount = 0

                    for k in range(7):
                        for l in range(7):
                            newX = i - 3 + k
                            newY = j - 3 + l 
                            if (newX - i) * (newX - i) + (newY - j) * (newY - j) < 10:
                                if self.map.is_path(newX, newY):
                                    tmpCount += 1

                    bomber_list.append((tmpCount, i, j))

        bomber_list.sort(key=lambda x: x[0], reverse=True)

        return bomber_list

    
    def calculate_sniper(self):
        sniper_list = []
        for i in range(self.width):
            for j in range(self.height):
                if self.map.is_space(i, j):
                    tmpCount = 0

                    for k in range(15):
                        for l in range(15):
                            newX = i - 7 + k
                            newY = j - 7 + l 
                            if (newX - i) * (newX - i) + (newY - j) * (newY - j) < 60:

                                if self.map.is_path(newX, newY):
                                    tmpCount += 1
                    sniper_list.append((tmpCount, i, j))

        sniper_list.sort(key=lambda x: x[0], reverse=True)

        return sniper_list
    
    def calculate_solar(self):
        solar_list = []
        for i in self.calculate_sniper():
            solar_list.append(i)
        return solar_list

    def calculate_asteroids(self):
        asteroid = []
        for i in range(self.width):
            for j in range(self.height):
                if (self.map.is_asteroid(i, j)):
                    asteroid.append([i, j])
        return asteroid
    
    def calculate_blanks(self):
        space = []
        for i in range(self.width):
            for j in range(self.height):
                if (self.map.is_space(i, j)):
                    space.append([i, j])
        return space
    # ---- init functions ---- #

    # ---- turn ---- #

    def play_turn(self, rc: RobotController):
        self.update_vals(rc)

        # try to rush:
        if len(self.map.path) <= 30 or self.opponent_rushing(rc) or self.hp == 2500 and self.enemy_hp < 2500 and self.enemy_hp < self.enemy_hp_prev[-50]:
            print("Rushing")
            self.rushing = True
            self.rush(rc)
            self.towers_attack(rc)
            self.rushing = True
            return
        


        # try to rush early while selling farms
        # if rc.get_towers(self.team) >= self.rush_const:
        #     self.sell_farms(rc)


        if (self.check_init_phase(rc)):
            print("Initial")
            self.initial_phase(rc)
        
        elif (self.rebuilding):
            print("Rebuilding")
            self.rebuild(rc)
        
        elif (self.should_rush(rc) == False and self.should_rush_prev == True):
            print("\t\tRebuilding")
            self.rebuilding = True
            self.rebuild(rc)
       
        elif (self.should_rush(rc)):
            print("Rushing")
            if (len(self.post_rush_spaces) == 0):
                self.post_rush_spaces = self.sell_all_farms(rc)
            self.rush(rc)
            self.rushing = True
            self.should_rush_prev = True

            # sell all farms
        else:
            print("Defending")
            # play as if safe
            print(self.is_safe(rc))
            if self.should_farm(rc):
                self.build_solar(rc)

            elif (self.bomb_is_desirable(rc) and len(self.bomber_list) > 0):
                self.build_bomber(rc)
            elif (len(self.sniper_list) > 0):
                self.build_sniper(rc)
            elif (len(self.bomber_list) > 0):
                self.build_bomber(rc)
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
        if (self.rushing == True and self.enemy_hp == self.enemy_hp_prev[-200]): # REPLACE WITH 2*50*c
            self.rushing = False
            return False

        if (len(self.map.path) <= 30):
            self.rushing = True
            return True

        if len(self.bomber_list) == 0 and len(self.sniper_list) == 0:
            self.rushing = True
            return True
        
        # if they rush and we have worse defense, build defense?
        
        # if they rush and we have stronger defenses and stronger economy, build defense to match their economy then rush?
        
        # if 
        
        
        return False


    def stronger(self, rc): # return a pair of booleans (stronger economy, stronger defense) for APPROXIMATE enemy defense and economy (ignores reinforcers)
        enemy_defense = rc.get_towers(rc.get_enemy_team)
        numbombers = 0
        numsnipers = 0
        numfarms = 0
        for t in enemy_defense:
            if t.type() == TowerType.BOMBER:
                numbombers += 1
            elif t.type() == TowerType.GUNSHIP:
                numsnipers += 1
            elif t.type() == TowerType.SOLAR_FARM:
                numfarms += 1
        stronger_defense = self.defense_dpt_heuristic(self,rc) >= numbombers * TowerType.BOMBER.damage * 5 + numsnipers * TowerType.GUNSHIP.damage * 3
        stronger_income = 10 + 2 * self.solar_count >= 10 + 2 * numfarms
        return (stronger_income, stronger_defense)
        
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
    
    def defense_dpt_heuristic(self,rc):
        return self.bomber_count * TowerType.BOMBER.damage * 5 + self.sniper_count * TowerType.GUNSHIP.damage * 3

    def is_safe(self, rc):
        avg = self.debris_damage_needed(rc) ** (1/2)
        return avg <= self.defense_dpt_heuristic(rc)
    
    def should_farm(self, rc):
        print("farm: ", self.is_safe(rc) and self.get_total_offensive() > int(0.2 * self.solar_count))
        return self.is_safe(rc) and self.get_total_offensive() > int(0.2 * self.solar_count)

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
        if (len(self.solar_list) < 1):
            return False 
        top = self.solar_list[-1]
        while (not rc.is_placeable(self.team, top[1], top[2])):
            self.solar_list.pop()
            if (len(self.solar_list) == 0):
                return False
            top = self.solar_list[-1]
        
        if (rc.can_build_tower(TowerType.SOLAR_FARM, top[1], top[2])):                

            density = rc.sense_towers_within_radius_squared(self.team, top[1], top[2], 5)
            solar_density = [i for i in density if i.type == TowerType.SOLAR_FARM]
            reinforcer_density = [i for i in density if i.type == TowerType.REINFORCER]

            if len(solar_density) >= 3 and len(reinforcer_density) == 0 and self.reinforcer_count * 6 < self.solar_count and self.solar_count >= 10:
                if rc.can_build_tower(TowerType.REINFORCER, top[1], top[2]):
                    rc.build_tower(TowerType.REINFORCER, top[1], top[2])
                    self.solar_list.pop()
                    self.reinforcer_count += 1 
            else:
                self.solar_list.pop()
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
        (c,h) = self.compute_optimal_dps(rc)
        
        if rc.can_send_debris(c,h):
            rc.send_debris(c,h)
        else:
            print("nooooooo rip debris")


    def opponent_rushing(self, rc):
        debris = rc.get_debris(self.team)

        return len([d for d in debris if d.sent_by_opponent]) > 0

    def cost(self, c, h):
        if h/c <= 30:
            return max(int((h**2/c)/12)+1,200)
        elif h/c <= 80:
            return max(max(int(h**2/(12*c)),1)+1,200)
        elif h/c <= 120:
            return max(max(int(h**1.9/(8*c)),1)+1,200)
        return max(max(int(h**1.8/(4.6*c)),1)+1,200)

    def compute_damage(self, rc, cooldown):
        dmg = 0 

        for tower in rc.get_towers(self.enemy_team):
            bombTiles = self.bomber_arr[tower.x][tower.y]
            sniperTiles = self.sniper_arr[tower.x][tower.y]

            if tower.type == TowerType.BOMBER:
                dmg += 6 * ceil(bombTiles * cooldown / 15)
            elif tower.type == TowerType.GUNSHIP:
                dmg += 25 * ceil(sniperTiles * cooldown / 20) / 2
    
    def compute_optimal_dps(self, rc):
        result = -1
        result_hp = -1
        result_cd = -1

        for cd in range(1, 5):
            best = 0
            for hp in range(26, 801, 25):
                if self.cost(cd, hp) < self.curr_wealth:
                    best = hp
                else:
                    break
            if self.cost(cd, best) > result:
                result = self.cost(cd,best)
                result_hp = best
                result_cd = cd
        

        return (result_cd, result_hp)
            

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
                    self.sniper_count += 1  
                else:
                    spaces.append([x, y])

            elif (tower.type == TowerType.REINFORCER):
                x = tower.x 
                y = tower.y
                if (self.distances[x][y] >= 8):
                    rc.sell_tower(tower.id)   
                    spaces.append([x, y])    

        return spaces
