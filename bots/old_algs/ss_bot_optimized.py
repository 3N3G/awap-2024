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

        self.gunship_count = 0
        self.bomber_count = 0
        self.solar_count = 0
        self.iters = 0


        # print(self.gunship_list)
        # print(self.bomber_list)
        # print(self.map_arr)
        # print(self.solar_list)
    
    def calculate_bomber(self):
        self.bomber_list = []
        for i in range(self.height):
            for j in range(self.width):
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
    
    def calculate_solar(self):
        self.solar_list = []
        for i in range(self.height):
            for j in range(self.width):
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




    def play_turn(self, rc: RobotController):
        self.build_towers(rc)
        self.towers_attack(rc)

    def build_towers(self, rc: RobotController):
        if(rc.get_balance(rc.get_ally_team()) >= 2000 and self.iters % 4 != 0):
            self.build_bomber(rc)
            self.iters += 1
        elif (rc.get_balance(rc.get_ally_team()) >= 2000) :
            print("want solar")
            self.build_solar_farm(rc)
            self.iters += 1

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            # if tower.type == TowerType.GUNSHIP:
            #     rc.auto_snipe(tower.id, SnipePriority.FIRST)
            if tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    def build_bomber(self, rc: RobotController):
        top = self.bomber_list[0]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            self.bomber_list.pop(0)
            top = self.bomber_list[0]
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.bomber_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])

            self.bomber_count += 1

            # print(top[1], top[2])

    def build_gunship(self, rc: RobotController):
        top = self.gunship_list[0]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            self.gunship_list.pop(0)
            top = self.gunship_list[0]
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            self.gunship_list.pop(0)
            rc.build_tower(TowerType.GUNSHIP, top[1], top[2])

            self.gunship_count += 1

            # print(top[1], top[2])

    def build_solar_farm(self, rc: RobotController):
        top = self.solar_list[0]
        while not rc.is_placeable(rc.get_ally_team(), top[1], top[2]):
            self.solar_list.pop(0)
            top = self.solar_list[0]
        if (rc.can_build_tower(TowerType.SOLAR_FARM, top[1], top[2])):
            # print("BUILDING SOLAR FARM")
            self.solar_list.pop(0)
            rc.build_tower(TowerType.SOLAR_FARM, top[1], top[2])

            self.solar_count += 1

            # print(top[1], top[2])

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.STRONG)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)