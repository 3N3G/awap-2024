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

        self.gunship_count = 0
        self.bomber_count = 0

        print(self.gunship_list)
        print(self.bomber_list)
        # print(self.map_arr)
    
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
        
        if self.bomber_count >int(5 * self.gunship_count):
            self.build_gunship(rc)
        else:
            self.build_bomber(rc)
        self.towers_attack(rc)

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

    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.STRONG)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)