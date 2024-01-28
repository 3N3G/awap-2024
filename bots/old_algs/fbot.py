from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.height = map.height 
        self.width = map.width

        self.calculate_bomber()
        self.calculate_gunship()
        self.gunship_copy = []
        for i in self.calculate_gunship():
            self.gunship_copy.append(i)
        
        self.gunship_count = 0
        self.bomber_count = 0
        self.solar_count = 0

        self.calculate_distance()

        print(self.gunship_list)
        print(self.bomber_list)

        print(len(self.gunship_list))
        print(len(self.bomber_list))

        self.path_list = []
        self.space_list = []
        self.block_list = []
        self.parse_map()
        # print(self.map_arr)

    def parse_map(self):
        for i in range(0, self.height):
            # print(i)
            for j in range (0, self.width):
                # print(j)
                tile = self.map.tiles[i][j]

                # idx = self.get_unique_idx(i, j)

                if (tile == Tile.PATH):
                    self.path_list += [[i, j]]

                elif (tile == Tile.SPACE):
                    self.space_list += [[i, j]]

                else:
                    self.block_list += [[i, j]]
    
    def calculate_bomber(self):
        self.bomber_list = []
        for i in range(self.width):
            for j in range(self.height):
                if self.map.is_space(i, j):
                    tmpCount = 0

                    for k in range(7):
                        for l in range(7):
                            newX = i-3 + k
                            newY = j-3 + l 
                            if (newX - i) * (newX - i) + (newY - j) * (newY - j) < 10:
                                # in range
                                if self.map.is_path(newX, newY):
                                    print(newX,newY)

                                    tmpCount += 1

                    self.bomber_list.append((tmpCount, i, j))

        self.bomber_list.sort(key=lambda x: x[0], reverse=True)

        return self.bomber_list

    def calculate_gunship(self):
        self.gunship_list = []
        for i in range(self.width):
            for j in range(self.height):
                if self.map.is_space(i, j):
                    tmpCount = 0

                    for k in range(15):
                        for l in range(15):
                            newX = i-7 + k
                            newY = j-7 + l 
                            if (newX - i) * (newX - i) + (newY - j) * (newY - j) < 60:
                                # in range
                                if self.map.is_path(newX, newY):
                                    tmpCount += 1

                    self.gunship_list.append((tmpCount, i, j))

        self.gunship_list.sort(key=lambda x: x[0], reverse=True)

        return self.gunship_list

    def is_safe(self, rc):
        # total = 0
        # debris = rc.get_debris(rc.get_ally_team())
        # for d in debris:
        #     total += d.health
        # avg = total / len(debris)
        
        avg = self.debris_damage_needed(rc) ** (1/2)
        # print(avg)

        # print(self.bomber_count * TowerType.BOMBER.damage * 5 + self.gunship_count * TowerType.GUNSHIP.damage * 3)
        return avg <= self.bomber_count * TowerType.BOMBER.damage * 5 + self.gunship_count * TowerType.GUNSHIP.damage * 3

    def play_turn(self, rc: RobotController):
        safe = self.is_safe(rc)
        hp = rc.get_health(rc.get_ally_team())
        enemy_hp = rc.get_health(rc.get_enemy_team())

        if (hp == 2500 and enemy_hp < 2500):
            if (rc.get_balance(rc.get_ally_team()) >= 5796):
                self.send_debris(rc)

                print(self.bomber_list)

        # if rc.get_turn() % 100 == 0:
        #     print(rc.get_turn())

        
        if safe and hp == 2500 and self.bomber_count > int(0.3 * self.solar_count) and len(self.gunship_list) > 0:
            self.build_solar(rc)
        
        else:
            if (len(self.bomber_list) > 0):
                self.build_bomber(rc)
            elif (len(self.gunship_list) > 0):
                self.build_bomber(rc)
            else:
                self.delete_farm_calc(rc)
                self.calculate_bomber()
                self.calculate_gunship()
                
            
            if not safe and len(self.gunship_list) > 0:
                self.build_gunship(rc)
            # elif self.bomber_count > int(1 * self.gunship_count) and len(self.gunship_list) > 0:
            #     self.build_gunship(rc)
            elif len(self.bomber_list) > 0:
                self.build_bomber(rc)
            elif (safe):
                self.send_debris(rc)
                
                    # self.spend_all_on_debris(rc)


        self.towers_attack(rc)

    def send_debris(self, rc: RobotController):
        if rc.can_send_debris(112, 2791):
            rc.send_debris(112, 2791)
            return True
        return False

    def build_solar(self, rc: RobotController):
        top = self.gunship_list[-1]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            print("NOT is_placeable")
            self.gunship_list.pop()
            top = self.gunship_list[-1]
        if (rc.can_build_tower(TowerType.SOLAR_FARM, top[1], top[2])):
            self.gunship_list.pop()
            rc.build_tower(TowerType.SOLAR_FARM, top[1], top[2])

            self.solar_count += 1

    def build_bomber(self, rc: RobotController):
        top = self.bomber_list[0]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            print("NOT is_placeable")
            self.bomber_list.pop(0)
            top = self.bomber_list[0]
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.bomber_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])

            self.bomber_count += 1

            # print(top[1], top[2])

    def adj_to_path(self, x, y):
        return ([x-1, y] in self.path_list or [x+1, y] in self.path_list or [x, y-1] in self.path_list or[x, y+1] in self.path_list)

    def build_gunship(self, rc: RobotController):
        top = self.gunship_list[0]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            print("NOT is_placeable")
            self.gunship_list.pop(0)
            top = self.gunship_list[0]
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            gunshipListLen = len(self.gunship_list)
            bestIndex = 0
            
            for i in range(int(0.2 * gunshipListLen)):
                x = self.gunship_list[i][1]
                y = self.gunship_list[i][2]

                if self.distances[x][y] < self.distances[self.gunship_list[bestIndex][1]][self.gunship_list[bestIndex][2]]:
                    bestIndex = i

            top = self.gunship_list[bestIndex]
            self.gunship_list.pop(bestIndex)
            
            if (not self.adj_to_path(top[1], top[2])):
                rc.build_tower(TowerType.GUNSHIP, top[1], top[2])
            else:
                while not (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
                    print("waiting for money: ", end = "")
                    print(rc.get_balance(self.get_ally_team()))
                rc.build_tower(TowerType.BOMBER, top[1], top[2])
            

            self.gunship_count += 1

            # print(top[1], top[2])

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    def debris_damage_needed(self, rc: RobotController):
        debris = rc.get_debris(rc.get_ally_team())
        hp = 0
        numballoons = 0
        for d in debris:
            hp = hp + d.health**2
            numballoons = numballoons + 1
        hp = hp // numballoons
        return hp
    
    def delete_farm_calc(self, rc):
        towers = rc.get_towers(rc.get_ally_team())
        temp = self.gunship_copy[int(0.9 * len(self.gunship_copy)) :]
        for i in temp:
            for tower in towers:
                if (tower.type == TowerType.SOLAR_FARM and i[1] == tower.x and i[2] == tower.y):
                    rc.sell_tower(tower.id)
                    break
    
    def spend_all_on_debris(self, rc):
        while (self.send_debris(rc)):
            print("sending debris!")

    def calculate_distance(self):
        self.distances = []
        for i in range(self.width):
            self.distances.append([])
            for j in range(self.height):
                curmin = 10000
                for (x,y) in self.map.path:
                    if self.map.is_path(i, j):
                        if(abs(i - x) + abs(j - y) < curmin):
                            curmin = abs(i - x) + abs(j - y)
                    if self.map.is_path(i, j):
                        if(abs(i - x) + abs(j - y) < curmin):
                            curmin = abs(i - x) + abs(j - y)
                self.distances[i].append(curmin)
