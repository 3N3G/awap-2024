from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower


c = 1
h = 100
# income = 10

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.height = map.height 
        self.width = map.width

        self.calculate_distance()
        self.calculate_bomber()
        self.calculate_gunship()
        self.solar_list = []
        for i in self.calculate_gunship():
            self.solar_list.append(i)

        # income = 10
        self.gunship_count = 0
        self.bomber_count = 0
        self.solar_count = 0
        self.enemy_hp_last = 2500


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
                    # if self.distances[i][j] == 1:
                    tmpCount -= int(2 / self.distances[i][j])
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

    def rush(self, rc):
        i = 0
        h = 100# int(2.33 * income**(0.55)) # inverse of cost function for c=1
        while (rc.can_send_debris(c, h) and i < 2*(rc.get_health(rc.get_enemy_team()))//h):
            rc.send_debris(c, h)
            # income += self.cost(c, h)
            i += 1

    def cost(c,h):
        if h/c <= 30:
            return int((h**2/c)/12)+1
        elif h/c <= 80:
            return max(int(h**2/(12*c)),int(h**(19/10)/(8*c)))+1
        elif h/c <= 120:
            return max(int(h**1.9/(8*c)),int(h**1.8/(4.6*c)))+1
        return max(int(h**1.8/(4.6*c)),int(h**1.6/(2*c)))+1


    def play_turn(self, rc: RobotController):
        # income = get_balance(self.get_ally_team)
        rushing = self.opponent_rushing(rc)
        if (rushing):
            self.rush(rc)
            self.towers_attack(rc)
            return

        safe = self.is_safe(rc)
        hp = rc.get_health(rc.get_ally_team())
        enemy_hp = rc.get_health(rc.get_enemy_team())

        if (hp == 2500 and enemy_hp < 2500):
            self.rush(rc)

        self.play_given_safe(rc, safe, hp)
        self.towers_attack(rc)
        # income = income - self.balance 
    
    def opponent_rushing(self, rc):
        debris = rc.get_debris(rc.get_ally_team())
        rushing = False

        # opponent_count = 0
        # total = 0
        for d in debris:
            if d.sent_by_opponent:
                rushing = True
                break
                # opponent_count+= 1
            # total+=1
        return rushing
        # if (rushing):
        # # if (opponent_count / total > 0.4):
        #     self.build_gunship(rc)
    
    def play_given_safe(self, rc, safe, hp):
        # print(len(self.bomber_list))
        if hp == 2500 and self.bomber_count > int(0.2 * self.solar_count):
            # print(self.solar_count)
            if (self.solar_count > 0 and self.solar_count % 5 == 0):
                self.build_reinforcer(rc)
            else:
                print("WANT TO BULID")
                self.build_solar(rc)
        
        # print(len(self.bomber_list))
        # if (len(self.bomber_list) == 0 and len(self.gunship_list) == 0):
        #     print("RUSHING")
        #     self.sell_all_farms(rc)
        #     self.rush(rc)

        if(True):
            if safe:
                if (len(self.bomber_list) > 0):
                    self.build_bomber(rc)
                elif (len(self.bomber_list) > 0):
                    self.build_gunship(rc)

            
            else:
                if (len(self.gunship_list) > 0):
                    self.build_gunship(rc)
                elif (len(self.bomber_list) > 0):
                    self.build_bomber(rc)
                    # income += 1750

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
            print("BUILDING SOLAR")
            self.gunship_list.pop()
            rc.build_tower(TowerType.SOLAR_FARM, top[1], top[2])

            self.solar_count += 1
        # top = self.solar_list[-1]
        # while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
        #     print("NOT is_placeable")

        #     self.solar_list.pop()
        #     self.gunship_list.remove(top)

        #     if (len(self.solar_list) == 0):
        #         return
        #     top = self.solar_list[-1]
        # if (rc.can_build_tower(TowerType.SOLAR_FARM, top[1], top[2])):
            
        #     self.solar_list.pop()
        #     self.gunship_list.remove(top)
            
        #     print("BUILDING SOLAR")
        #     rc.build_tower(TowerType.SOLAR_FARM, top[1], top[2])
        #     income += 2000

        #     self.solar_count += 1

    def build_reinforcer(self, rc: RobotController):
        top = self.solar_list[-1]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            print("NOT is_placeable")
            
            self.solar_list.pop()
            self.gunship_list.remove(top)

            if (len(self.solar_list) == 0):
                return
            top = self.solar_list[-1]
        if (rc.can_build_tower(TowerType.REINFORCER, top[1], top[2])):
            
            self.solar_list.pop()
            self.gunship_list.remove(top)

            rc.build_tower(TowerType.REINFORCER, top[1], top[2])
            # income += 3000

            self.solar_count += 1

    def build_bomber(self, rc: RobotController):
        top = self.bomber_list[0]
        
        # check that 
        while (not rc.is_placeable(rc.get_ally_team(), top[1], top[2]) or top[0] == 0):
            self.bomber_list.pop(0)
            if (len(self.bomber_list) == 0):
                return
            top = self.bomber_list[0]
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.bomber_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])
            # income += 1750

            self.bomber_count += 1

            # print(top[1], top[2])

    def build_gunship(self, rc: RobotController):
        top = self.gunship_list[0]
        while (not rc.is_placeable(rc.get_ally_team(), top[1], top[2]) or top[0] == 0):

            self.gunship_list.pop(0)
            # self.solar_list.remove(top)

            if (len(self.gunship_list) == 0):
                return
            top = self.gunship_list[0]
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            # gunshipListLen = len(self.gunship_list)
            # bestIndex = 0
            
            # for i in range(int(0.1 * gunshipListLen)):
            #     x = self.gunship_list[i][1]
            #     y = self.gunship_list[i][2]

            #     if self.distances[x][y] < self.distances[self.gunship_list[bestIndex][1]][self.gunship_list[bestIndex][2]]:
            #         bestIndex = i

            # top = self.gunship_list[bestIndex]

            self.gunship_list.pop(0)
            # self.solar_list.remove(top)

            rc.build_tower(TowerType.GUNSHIP, top[1], top[2])
            # income += 1000

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
        if (numballoons == 0):
            return 0
        hp = hp // numballoons
        return hp

    
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
        return len(self.map.path) <= 30
        # send ~5000 hp worth of debris

    def sell_all_farms(self, rc):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if (tower.id == TowerType.SOLAR_FARM or tower.id == TowerType.REINFORCER):
                rc.sell_tower(tower.id)