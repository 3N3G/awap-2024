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
        while(rc.can_send_debris(3, 90)):
            rc.send_debris(3, 90)

        # better?
        # while(rc.can_send_debris(12, 180)):
        #     rc.send_debris(12, 180)
        