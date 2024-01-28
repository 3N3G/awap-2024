import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map

    def play_turn(self, rc: RobotController):
        # raffle rush
        # while(rc.can_send_debris(3, 90)):
        #     rc.send_debris(3, 90)

        # better?
        
        cd = 4
        hp = 0

        if cd == 1: 
            hp = 50
        elif cd == 2: 
            hp = 70
        elif cd == 3:
            hp = 85
        elif cd == 4:
            hp = 100
        elif cd == 5:
            hp = 110
        elif cd == 6:
            hp = 120
        elif cd == 7:
            hp = 130
        elif cd == 8:
            hp = 140
        
        while (rc.can_send_debris(cd,hp)):
            rc.send_debris(cd,hp)