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
        self.calculate_solar()
        # self.calculate_reinforcer()
        self.reinforcer_list = []

        self.gunship_count = 0
        self.bomber_count = 0
        self.solar_count = 0
        self.reinforcer_count = 0
        self.iters = 0
        self.just_attack = True

        self.desired = TowerType.SOLAR_FARM
        self.team = None
        self.r_calc = True
        self.first = True


        # print(self.gunship_list)
        # print(self.bomber_list)
        # print(self.map_arr)
        print(self.solar_list)
    
    def play_turn(self, rc: RobotController):
        self.team = rc.get_ally_team()
        self.build_towers(rc)
        self.towers_attack(rc)
    
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
    
    def calculate_reinforcer(self, rc):
        max = 0
        best = self.gunship_list[0]
        for i in self.gunship_list:
            towers = len(rc.sense_towers_within_radius_squared(self.team, i[1], i[2], 5))
            if (towers > max):
                best = i
                max = towers
        
        self.gunship_list.remove(best)
        return best
        # for i in range(self.height):
        #     for j in range(self.width):
        #         if self.map.is_space(i, j):
        #             tmpCount = 0

        #             for k in range(5):
        #                 for l in range(5):
        #                     newX = i-2 + k
        #                     newY = j-2 + l 
        #                     if (newX - i) * (newX - i) + (newY - j) * (newY - j) < 10:
        #                         # in range
        #                         if self.map.is_path(newX, newY):
        #                             print(newX,newY)

        #                             tmpCount += 1

        #             self.reinforcer_list.append((tmpCount, i, j))

        # self.reinforcer_list.sort(key=lambda x: x[0], reverse=True)

        return self.reinforcer_list
    
    def calculate_solar(self):
        self.solar_list = []
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

                    self.solar_list.append((tmpCount, i, j))

        self.solar_list.sort(key=lambda x: x[0], reverse=False)

        return self.solar_list

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


    def build_towers(self, rc: RobotController):
        bal = rc.get_balance(self.team)
        enemy_hp = rc.get_health(rc.get_enemy_team())

        if (rc.get_health(self.team) < 2500):
            self.build_gunship()

        if (self.iters < 5 and self.first == True):
            if (self.build_solar_farm(rc)):
                self.iters += 1
        elif (self.iters == 5):
            self.first = False
            self.iters = 16
            self.desired = TowerType.BOMBER

        if (self.desired == TowerType.SOLAR_FARM):
            if (self.build_solar_farm(rc)):
                self.iters += 1
                if (self.iters % 10 > 6):
                    self.desired = TowerType.BOMBER
        elif (self.desired == TowerType.BOMBER):
            if (self.build_bomber(rc)):
                self.iters += 1
                if (self.iters % 10 > 8):
                    self.desired = None
        # elif (self.desired == TowerType.REINFORCER):
        #     print("WANT REINFORCER")
        #     if (self.build_reinforcer(rc)):
        #         self.iters += 1
        #         self.desired = None
        #         self.r_calc = True
        elif (self.desired == None):
            if (enemy_hp < 2500):
                if (bal >= 5796):
                    rc.send_debris(112, 2791)
                    self.iters += 1
                    self.desired = TowerType.SOLAR_FARM
            else:
                self.desired = TowerType.SOLAR_FARM
                if (self.build_solar_farm(rc)):
                    self.iters += 1
                    if (self.iters % 10 > 1):
                        self.desired = TowerType.BOMBER


        # if (bal >= 2000 and self.iters % 10 == 0 or self.iters % 10 == 1) :
        #     print("want solar")
        #     self.build_solar_farm(rc)
        #     self.iters += 1
        
        # if (bal >= 2000 and self.iters % 10 == 0 or self.iters % 10 == 1) :

        # elif (bal >= 2000):
        #     self.build_bomber(rc)
        #     self.iters += 1
        

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(self.team)
        for tower in towers:
            # if tower.type == TowerType.GUNSHIP:
            #     rc.auto_snipe(tower.id, SnipePriority.FIRST)
            if tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    def build_bomber(self, rc: RobotController):
        top = self.bomber_list[0]
        while not rc.is_placeable(self.team, top[1], top[2]):
            self.bomber_list.pop(0)
            top = self.bomber_list[0]
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.bomber_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])

            self.bomber_count += 1
            self.just_attack = False
            return True
        return False

            # print(top[1], top[2])
    
    def build_reinforcer(self, rc: RobotController):
        top = self.gunship_list[0]
        while not rc.is_placeable(self.team, top[1], top[2]):
            self.gunship_list.pop(0)
            top = self.gunship_list[0]
        if (rc.can_build_tower(TowerType.REINFORCER, top[1], top[2])):
            self.gunship_list.pop(0)
            rc.build_tower(TowerType.REINFORCER, top[1], top[2])

            self.reinforcer_count += 1
            return True
        return False

        # if (rc.can_build_tower(TowerType.REINFORCER, desired[1], desired[2])):
        #     self.bomber_list.pop(0)
        #     rc.build_tower(TowerType.REINFORCER, desired[1], desired[2])

        #     self.reinforcer_count += 1
        #     return True
        # return False

    def build_gunship(self, rc: RobotController):
        top = self.gunship_list[0]
        while not rc.is_placeable(self.team, top[1], top[2]):
            self.gunship_list.pop(0)
            top = self.gunship_list[0]
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            self.gunship_list.pop(0)
            rc.build_tower(TowerType.GUNSHIP, top[1], top[2])

            self.gunship_count += 1
            return True
        return False

            # print(top[1], top[2])

    def build_solar_farm(self, rc: RobotController):
        top = self.solar_list[0]
        while not rc.is_placeable(self.team, top[1], top[2]):
            self.solar_list.pop(0)
            top = self.solar_list[0]
        if (rc.can_build_tower(TowerType.SOLAR_FARM, top[1], top[2])):
            print("BUILDING SOLAR FARM")
            self.solar_list.pop(0)
            rc.build_tower(TowerType.SOLAR_FARM, top[1], top[2])

            self.solar_count += 1
            return True
        return False

            # print(top[1], top[2])

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(self.team)
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.STRONG)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)