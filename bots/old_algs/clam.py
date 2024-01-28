from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower
import math

from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower
import math

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.count = 0
        self.sniperpositions = self.mostpath(7, True, self.map.width*self.map.height)
        self.bomberpositions = self.mostpath(3, True, self.map.width*self.map.height)
        self.sunpositions = self.mostpath(7, False, self.map.width*self.map.height)
        self.villagepositions = self.mostspaces(2, True, self.map.width*self.map.height)
        self.attack = -3
        self.solar = 0
        self.ratio = 1
        self.bomb_multiplier = 4
        self.startbuilding = False
        self.villagex = 2
        self.villagey = 2
        print(map.path_length)
        self.placedsun = []
        self.solarzero = 0
        if(map.path_length<70):
            self.bomb_multiplier = 2


    def play_turn(self, rc: RobotController):
        self.build_towers(rc)
        self.towers_attack(rc)

    def build_towers(self, rc: RobotController):
        locations = self.sniperpositions.index(max(self.sniperpositions))
        locationb = self.bomberpositions.index(max(self.bomberpositions))
        locationsun = self.sunpositions.index(min(self.sunpositions))
        if(self.attack==0):
            self.startbuilding = True
        if(self.counter ==0):
            if(self.solarzero < len(self.placedsun)):
                x = self.indextorow(self.placedsun[len(self.placedsun)-1])
                y = self.indextocol(self.placedsun[len(self.placedsun)-1])
                towertosell = rc.sense_towers_within_radius_squared(rc.get_ally_team(), x, y, 0)
                rc.sell_tower(towertosell[0].id)
                self.placedsun.pop(len(self.placedsun)-1)
                if (rc.can_build_tower(TowerType.GUNSHIP, x, y)):
                    rc.build_tower(TowerType.GUNSHIP, x, y)
            elif(self.villagex<self.map.width and self.villagey<self.map.height):
                if(self.villagepositions[self.rowcoltoindex(self.villagey, self.villagex)]>=7):
                    towertosell = rc.sense_towers_within_radius_squared(rc.get_ally_team(), self.villagey, self.villagex, 0)
                    rc.sell_tower(towertosell[0].id)
                    if (rc.can_build_tower(TowerType.REINFORCER, self.villagey, self.villagex)):
                        rc.build_tower(TowerType.REINFORCER, self.villagey, self.villagex)
                self.villagex +=4
                if(self.villagex>self.map.width):
                    self.villagex = 2
                    self.villagey +=4
        else:
            if((len(rc.get_debris(rc.get_ally_team()))<(self.map.path_length/4) and
                min(self.sunpositions)==0
                or self.attack==self.ratio)
                and self.startbuilding):
                if (rc.can_build_tower(TowerType.SOLAR_FARM, self.indextorow(locationsun), self.indextocol(locationsun))):
                    rc.build_tower(TowerType.SOLAR_FARM, self.indextorow(locationsun), self.indextocol(locationsun))
                    self.bomberpositions[locationsun] = -1
                    self.sniperpositions[locationsun] = -1
                    self.sunpositions[locationsun] = 2305
                    self.attack = 0
                    self.solar += 1
                    self.counter -= 1
                    self.placedsun.append(locationsun)
                    if(min(self.sunpositions)==0):
                        self.solarzero += 1
            else:
                if(max(self.bomberpositions)*self.bomb_multiplier>max(self.sniperpositions)):
                    if (rc.can_build_tower(TowerType.BOMBER, self.indextorow(locationb), self.indextocol(locationb))):
                        rc.build_tower(TowerType.BOMBER, self.indextorow(locationb), self.indextocol(locationb))
                        self.bomberpositions[locationb] = -1
                        self.sniperpositions[locationb] = -1
                        self.sunpositions[locationb] = 2305
                        self.attack += 1
                        self.counter -= 1
                else:
                    if (rc.can_build_tower(TowerType.GUNSHIP, self.indextorow(locations), self.indextocol(locations))):
                        rc.build_tower(TowerType.GUNSHIP, self.indextorow(locations), self.indextocol(locations))
                        self.sniperpositions[locations] = -1
                        self.bomberpositions[locations] = -1
                        self.sunpositions[locations] = 2305
                        self.attack += 1
                        self.counter -= 1
                
    def indextorow(self, index:int):
        return index//self.map.width
    def indextocol(self, index:int):
        return index%self.map.width
    def rowcoltoindex(self, row:int, col:int):
        return row*self.map.width + col

    def mostpath(self, radius: int, is_max: bool, numreturn: int):
        path = []
        self.counter = 0
        for location in range(self.map.width *self.map.height):
            row = self.indextorow(location)
            col = self.indextocol(location)
            if(self.map.is_space(row, col)):
                numberpath = 0
                for a in range(2*radius):
                    for b in range(2*radius):
                        if (math.dist([a-radius,b-radius], [0, 0])< radius) and row+a-radius>=0 and col+b-radius>=0:
                            if self.map.is_path(row+a-radius,col+b-radius):
                                numberpath = numberpath + 1
                path.append(numberpath)
                self.counter +=1
            else:
                if is_max:
                    path.append(-1)
                else:
                    path.append(48*48+1)
        """returningstuff = []
        for i in range(numreturn):
            if is_max:
                returningstuff.append(path.index(max(path)))
                path.pop(path.index(max(path)))
            else:
                returningstuff.append(path.index(min(path)))
                path.pop(path.index(min(path)))
        print(returningstuff)
        """
        return path
    
    def mostspaces(self, radius: int, is_max: bool, numreturn: int):
        path = []
        self.counter = 0
        for location in range(self.map.width *self.map.height):
            row = self.indextorow(location)
            col = self.indextocol(location)
            if(self.map.is_space(row, col)):
                numberpath = 0
                for a in range(2*radius):
                    for b in range(2*radius):
                        if (math.dist([a-radius,b-radius], [0, 0])< radius) and row+a-radius>=0 and col+b-radius>=0:
                            if self.map.is_space(row+a-radius,col+b-radius):
                                numberpath = numberpath + 1
                path.append(numberpath)
                self.counter +=1
            else:
                if is_max:
                    path.append(-1)
                else:
                    path.append(48*48+1)
        return path
            

    
    def towers_attack(self, rc: RobotController):
        #Random
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)