import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map

    def play_turn(self, rc: RobotController):
        self.build_towers(rc)
        self.towers_attack(rc)

    def build_towers(self, rc: RobotController):
        int timeleft = get_time_remaining_at_start_of_turn(rc.get_ally_team())
        x = random.randint(0, self.map.height-1)
        y = random.randint(0, self.map.height-1)
        tower = random.randint(1, 4) # randomly select a tower
        if (rc.can_build_tower(TowerType.SOLAR_FARM, x, y) and 
            rc.can_build_tower(TowerType.BOMBER, x, y)
        ):
            if tower == 1 or 3:
                rc.build_tower(TowerType.SOLAR_FARM, x, y)
            elif tower == 2 or 4:
                rc.build_tower(TowerType.BOMBER, x, y)

        while(rc.can_send_debris(7, 1000)):
            rc.send_debris(7, 1000)
    
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
