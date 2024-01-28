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
        # print(self.map_arr)
    
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
        print(avg)

        print(self.bomber_count * TowerType.BOMBER.damage * 5 + self.gunship_count * TowerType.GUNSHIP.damage * 3)
        return avg <= self.bomber_count * TowerType.BOMBER.damage * 5 + self.gunship_count * TowerType.GUNSHIP.damage * 3

    def rush(self, rc):
        i = 0
        while (rc.can_send_debris(3, 90)):
            rc.send_debris(3, 90)
            i += 1

    def cost(c,h):
        if h/c <= 30:
            return int((h**2/c)/12)+1
        elif h/c <= 80:
            return max(int(h**2/(12*c)),int(h**(19/10)/(8*c)))+1
        elif h/c <= 120:
            return max(int(h**1.9/(8*c)),int(h**1.8/(4.6*c)))+1
        return max(int(h**1.8/(4.6*c)),int(h**1.6/(2*c)))+1

    c = 3
    h = 90
    # VICTORIA UPDATE THESE

    def play_turn(self, rc: RobotController):
        if (self.should_rush and rc.get_turn() < ):
            self.rush(rc)
            return
        
        self.opponent_rushing(rc)

        safe = self.is_safe(rc)
        hp = rc.get_health(rc.get_ally_team())
        enemy_hp = rc.get_health(rc.get_enemy_team())
        if (hp == 2500 and enemy_hp < 2500):
            if (rc.get_balance(rc.get_ally_team()) >= 5796):
                self.send_debris(rc)

                print(self.bomber_list)

        if rc.get_turn() % 100 == 0:
            print(rc.get_turn())

        
        self.play_given_safe(rc, safe, hp)
        self.towers_attack(rc)
    
    def opponent_rushing(self, rc):
        debris = rc.get_debris(rc.get_ally_team())

        opponent_count = 0
        total = 0
        for d in debris:
            if d.sent_by_opponent:
                opponent_count+= 1
            total+=1
        
        if (opponent_count / total > 0.4):
            self.build_gunship(rc)
    
    def play_given_safe(self, rc, safe, hp):
        if safe and hp == 2500 and self.bomber_count > int(0.2 * self.solar_count) and len(self.gunship_list) > 0:
            self.build_solar(rc)
        
        else:
            if (len(self.bomber_list) > 0):
                self.build_bomber(rc)
            else:
                self.delete_farm_calc(rc)
                self.spend_all_on_debris(rc)
                self.calculate_bomber()
                self.calculate_gunship()
                
            
            if not safe:
                self.build_gunship(rc)
            # elif self.bomber_count > int(1 * self.gunship_count) and len(self.gunship_list) > 0:
            #     self.build_gunship(rc)
            elif len(self.bomber_list) > 0:
                self.build_bomber(rc)
            elif (safe):
                self.send_debris(rc)

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
            if (len(self.gunship_list) == 0):
                return
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
            if (len(self.bomber_list) == 0):
                return
            top = self.bomber_list[0]
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.bomber_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])

            self.bomber_count += 1

            # print(top[1], top[2])

    def build_gunship(self, rc: RobotController):
        top = self.gunship_list[0]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            print("NOT is_placeable")
            self.gunship_list.pop(0)
            if (len(self.gunship_list) == 0):
                return
            top = self.gunship_list[0]
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            gunshipListLen = len(self.gunship_list)
            bestIndex = 0
            
            for i in range(int(0.2 * gunshipListLen)):
                x = self.gunship_list[i][1]
                y = self.gunship_list[i][2]

                if self.distances[x][y] < self.distances[self.gunship_list[bestIndex][1]][self.gunship_list[bestIndex][2]]:
                    bestIndex = i

            top = self.gunship_list[i]
            self.gunship_list.pop(i)
            rc.build_tower(TowerType.GUNSHIP, top[1], top[2])

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

    def should_rush(self):
        return len(self.map.path) <= 60
        # send ~5000 hp worth of debris