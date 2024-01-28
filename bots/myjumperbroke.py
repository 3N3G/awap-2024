import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

import numpy as np
from scipy.spatial import cKDTree

class SpatialIndex:
    def __init__(self):
        self.kd_tree = cKDTree([(-4,-4)])
        self.points = []

    def insert_point(self, point):
        self.points.append(point)
        if self.points[0][0] < 0:
            self.points.pop(0)
        self.kd_tree = cKDTree(self.points)

    def query_point(self, x,y):
        neighbors = self.kd_tree.query_ball_point((x,y), np.sqrt(5))
        count = sum(1 for neighbor in neighbors)
        return count

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.gunners, gunners_dict = self.count_target_tiles_within_radius(map.height, map.width, map.path, np.sqrt(60))
        self.bombs, bombs_dict = self.count_target_tiles_within_radius(map.height, map.width, map.path, np.sqrt(10))
        self.bomb_spots = list(filter(lambda x: map.is_space(x[1], x[0]), sorted(gunners_dict, key=lambda x: -bombs_dict[x])))
        self.gun_spots = list(filter(lambda x: map.is_space(x[1], x[0]), sorted(gunners_dict, key=lambda x: -gunners_dict[x])))
        self.bomb_pointer = 0
        self.farm_pointer = len(self.gun_spots)-1
        self.gun_pointer = 0
        self.tower_ids = np.empty((map.height, map.width))
        self.first = True
        self.max_cool = 0
        self.path = {}
        n = len(map.path)
        for i in range(len(map.path)):
            self.path[map.path[i]] = 2/(1 + np.exp(-np.log(n) * ((i+1) - n * 0.65))) + 1
        self.farm_locs = SpatialIndex()
        self.attack_locs = SpatialIndex()
        self.support = 0
        self.farm_cap = False
        self.farm_reinforce = np.empty((map.height, map.width))
        self.counter = False
        
    
    def play_turn(self, rc: RobotController):
        if self.first:
            rc.send_debris(15, 190)
            self.first = False
        if self.counter and rc.get_balance(rc.get_ally_team()) > 580:
            rc.send_debris(1,85)
            return
        if rc.get_balance(rc.get_ally_team()) < 1000:
            self.towers_attack(rc)
            return 
        debris = rc.get_debris(rc.get_ally_team())
        badness = 0
        for d in debris:
            badness += d.health * max(21-d.total_cooldown, 1) * self.path[(d.x, d.y)]
            # if d.total_cooldown > self.max_cool:
            #     self.max_cool = d.total_cooldown
            
        
       

        # print(badness / len(self.map.path), self.expected_shots(rc))
        if badness / len(self.map.path) > self.expected_shots(rc) or self.farm_cap:
            
            # if rc.get_balance(rc.get_ally_team()) < 1000:
            #     break
            if len(self.gun_spots) - self.farm_pointer <= self.bomb_pointer + self.gun_pointer:
                if self.gun_pointer > 3 * self.bomb_pointer+1:
                    if self.bomb_pointer < len(self.bomb_spots):
                        bomb_spot = self.bomb_spots[self.bomb_pointer]
                        if self.bombs[bomb_spot] >= 7 and rc.get_balance(rc.get_ally_team()) > 1750:
                            if rc.can_build_tower(TowerType.BOMBER, bomb_spot[1], bomb_spot[0]):
                                rc.build_tower(TowerType.BOMBER, bomb_spot[1], bomb_spot[0])
                                self.attack_locs.insert_point((bomb_spot[1], bomb_spot[0]))
                                self.bomb_pointer += 1
                            else:
                                self.bomb_pointer += 1
                                
                else:
                    if self.gun_pointer < len(self.gun_spots):
                        gun_spot = self.gun_spots[self.gun_pointer]
                        if self.gunners[gun_spot] >= 15 and rc.get_balance(rc.get_ally_team()) > 1000:
                            if rc.can_build_tower(TowerType.GUNSHIP, gun_spot[1], gun_spot[0]):
                                rc.build_tower(TowerType.GUNSHIP, gun_spot[1], gun_spot[0])
                                self.attack_locs.insert_point((gun_spot[1], gun_spot[0]))
                                self.gun_pointer += 1
                            else:
                                self.gun_pointer += 1
            else:
                if ((self.bombs[self.bomb_spots[self.bomb_pointer]] ** 2) * 6 / 15 > self.gunners[self.gun_spots[self.gun_pointer]] * 25/ 20) and self.gun_pointer > 0.5 * self.bomb_pointer:
                    bomb_spot = self.bomb_spots[self.bomb_pointer]
                    if self.bombs[bomb_spot] >= 7 and rc.get_balance(rc.get_ally_team()) > 1750:
                        if rc.can_build_tower(TowerType.BOMBER, bomb_spot[1], bomb_spot[0]):
                            rc.build_tower(TowerType.BOMBER, bomb_spot[1], bomb_spot[0])
                            self.attack_locs.insert_point((bomb_spot[1], bomb_spot[0]))
                            self.bomb_pointer += 1
                        else:
                            self.bomb_pointer+= 1
                else:
                    gun_spot = self.gun_spots[self.gun_pointer]
                    if self.gunners[gun_spot] >= 15 and rc.get_balance(rc.get_ally_team()) > 1000:
                        if rc.can_build_tower(TowerType.GUNSHIP, gun_spot[1], gun_spot[0]):
                            rc.build_tower(TowerType.GUNSHIP, gun_spot[1], gun_spot[0])
                            self.attack_locs.insert_point((gun_spot[1], gun_spot[0]))
                            self.gun_pointer += 1
                        else:
                            self.gun_pointer += 1
        # else:
            # if rc.get_balance(rc.get_ally_team()) > 250:
            #     rc.send_debris(1, 51)
        if badness / len(self.map.path) > min(rc.get_health(rc.get_ally_team())/1.5 + self.expected_shots(rc), 2 * self.expected_shots(rc)):
            self.sell_farms(rc)
            # for t in rc.get_towers(rc.get_ally_team()):
            #     rc.sell_tower(t)
            # print(rc.get_balance(rc.get_ally_team()), "before")
            
            while rc.get_balance(rc.get_ally_team()) >= 1000 and badness / len(self.map.path) > self.expected_shots(rc):
                best_village = None
                best_hits = 0
                for i in range(self.gun_pointer, len(self.gun_spots)):
                    cand = self.gun_spots[i]
                    hits = self.attack_locs.query_point(cand[1], cand[0])
                    
                    if hits > best_hits:
                        best_hits = hits
                        best_village = cand
                if best_hits > 4:
                    if rc.get_balance(rc.get_ally_team()) >= 3000:
                        if rc.can_build_tower(TowerType.REINFORCER, best_village[1], best_village[0]):
                            rc.build_tower(TowerType.REINFORCER, best_village[1], best_village[0])
                            self.support += 1
                if self.gun_pointer > 3 * self.bomb_pointer+1:
                    if self.bomb_pointer < len(self.bomb_spots):
                        bomb_spot = self.bomb_spots[self.bomb_pointer]
                        if self.bombs[bomb_spot] >= 7 and rc.get_balance(rc.get_ally_team()) > 1750:
                            if rc.can_build_tower(TowerType.BOMBER, bomb_spot[1], bomb_spot[0]):
                                rc.build_tower(TowerType.BOMBER, bomb_spot[1], bomb_spot[0])
                                self.attack_locs.insert_point((bomb_spot[1], bomb_spot[0]))
                                self.bomb_pointer += 1
                                continue
                            else:
                                self.bomb_pointer += 1
                                continue
                    else:
                        break

                if self.gun_pointer < len(self.gun_spots):
                    gun_spot = self.gun_spots[self.gun_pointer]
                    if self.gunners[gun_spot] >= 15 and rc.get_balance(rc.get_ally_team()) > 1000:
                        if rc.can_build_tower(TowerType.GUNSHIP, gun_spot[1], gun_spot[0]):
                            rc.build_tower(TowerType.GUNSHIP, gun_spot[1], gun_spot[0])
                            self.attack_locs.insert_point((gun_spot[1], gun_spot[0]))
                            self.gun_pointer += 1
                            continue
                        else:
                            self.gun_pointer += 1
                            continue
                    

                break
            # print(rc.get_balance(rc.get_ally_team()), "after")
            self.towers_attack(rc)
            return

        
        if len(self.gun_spots) - self.farm_pointer >= 1.25 * (self.bomb_pointer + self.gun_pointer + self.support) and rc.get_balance(rc.get_ally_team()) >= 3000:
            best_village = None
            best_hits = 0
            for i in range(self.gun_pointer, len(self.gun_spots)):
                cand = self.gun_spots[i]
                hits = self.attack_locs.query_point(cand[1], cand[0])
                if hits > best_hits:
                    best_hits = hits
                    best_village = cand
            if best_hits > 4:
                if rc.get_balance(rc.get_ally_team()) >= 3000:
                    if rc.can_build_tower(TowerType.REINFORCER, best_village[1], best_village[0]):
                        rc.build_tower(TowerType.REINFORCER, best_village[1], best_village[0])
                        self.support += 1

        for i in range(self.farm_pointer, -1, -1):
            if rc.get_balance(rc.get_ally_team()) < 2000:
                break
            k = self.gun_spots[i]
            if self.gunners[k] >= 0.35 * len(self.map.path):
                self.farm_cap = True
                break
            if self.farm_locs.query_point(k[1], k[0]) > 6:
                if rc.get_balance(rc.get_ally_team()) < 3000:
                    break
                if rc.can_build_tower(TowerType.REINFORCER, k[1], k[0]):
                    rc.build_tower(TowerType.REINFORCER, k[1], k[0])
                    self.farm_reinforce[k[0], k[1]] = 1
                    self.farm_pointer -= 1
                continue
            if rc.can_build_tower(TowerType.SOLAR_FARM, k[1], k[0]):
                rc.build_tower(TowerType.SOLAR_FARM, k[1], k[0])
                self.farm_locs.insert_point((k[1], k[0]))
                self.farm_pointer -= 1
            else:
                break
        
        

        
        self.towers_attack(rc)
        # if rc.get_balance(rc.get_ally_team()) > 250:
        #     rc.send_debris(1,51)

        return

    def count_target_tiles_within_radius(self, rows, cols, target_tiles, radius):

        result = np.zeros((rows, cols))
        r_dict = {}

        tree = cKDTree(target_tiles)

        for y in range(rows):
            for x in range(cols):

                # Query the KD-tree for points within the radius
                neighbors = tree.query_ball_point((x,y), radius)

                # Count the number of target tiles within the radius
                count = sum(1 for neighbor in neighbors)

                result[y,x] = count
                r_dict[(y,x)] = count





        return result, r_dict
    
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

     
    def expected_shots(self, rc: RobotController):
        expected_snipes = 0
        expected_bombs = 0
        for k in rc.get_towers(rc.get_ally_team()):
            if k.type == TowerType.BOMBER:
                expected_bombs += self.bombs[k.y, k.x]/15
            elif k.type == TowerType.GUNSHIP:
                expected_snipes += self.gunners[k.y, k.x]/20
        return expected_snipes * 25 + expected_bombs * 6
    
    def sell_farms(self, rc: RobotController):
        self.farm_pointer = len(self.gun_spots) - 1
        self.farm_cap = False
        for k in rc.get_towers(rc.get_ally_team()):
            if k.type == TowerType.SOLAR_FARM:
                rc.sell_tower(k.id)
            if k.type == TowerType.REINFORCER:
                if self.farm_reinforce[k.y,k.x] == 1:
                    rc.sell_tower(k.id)
        self.farm_locs = SpatialIndex()
        self.farm_reinforce = np.empty((self.map.height, self.map.width))