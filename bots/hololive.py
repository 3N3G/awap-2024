from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower


c = 4
h = 100
# income = 10
prev_wealth = 1500
curr_wealth = 1500

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.height = map.height 
        self.width = map.width



    def play_turn(self, rc: RobotController):
        if rc.get_turn() > 500:
            rc.send_debris(4, 100)