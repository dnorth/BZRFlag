from bzrc import BZRC, Command
import math, numpy, argparse
from numpy import dot
from random import randint
from time import sleep

desc=''' Example:
    python kalman_pigeon.py -p localhost -s 57413 -t [1, 2, 3]
    '''

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # self.visited = False
    def __hash__(self):
        return hash((self.x, self.y))
    def __eq__(self, other):
        if not isinstance(other, Point):
            # print "I DID FALSE!"
            return False
        else:
            # print "I DID TRUE!"
            return (self.x, self.y) == (other.x, other.y)

class Agent(object):
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.tank = self.bzrc.get_mytanks()[0]
        self.commands = []
        self.constants = self.bzrc.get_constants()
        self.is_running = False
    def update(self):
        self.tank = self.bzrc.get_mytanks()[0]
    def type1(self):
        # basically do nothing
        self.is_running = False
    def type2(self):
        # constant x and y
        enemy = self.bzrc.get_othertanks()[0]
        randPoint = getRandomPoint(int(enemy.x), int(enemy.y))
        x = 0
        while True:
            self.update()
            turnToPosition(self.bzrc, self.tank, randPoint.x, randPoint.y)
            if facingAngle(self.tank, randPoint.x, randPoint.y):
                x += 1
            else:
                x = 0
            if x > 100:
                break
        self.bzrc.angvel(self.tank.index, 0)
        self.bzrc.speed(self.tank.index, 1)
    def type3(self):
        while True:
            self.update()
            enemy = self.bzrc.get_othertanks()[0]
            randPoint = getRandomPoint(int(enemy.x), int(enemy.y))
            moveToPosition(self.bzrc, self.tank, randPoint.x, randPoint.y)
            sleep(3)
    # def evalAndMove(self):

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    agent = Agent(bzrc)
    return bzrc, agent

def normalize_angle(angle):
    """Make any angle be between +/- pi."""
    from math import pi
    angle -= 2 * pi * int (angle / (2 * pi))
    if angle <= -pi:
        angle += 2 * pi
    elif angle > pi:
        angle -= 2 * pi
    return angle

def facingAngle(tank, target_x, target_y):
    target_angle = math.atan2(target_y - tank.y,
                    target_x - tank.x)
    relative_angle = normalize_angle(target_angle - tank.angle)
    return relative_angle < 0.5

def moveToPosition(bzrc, tank, target_x, target_y):
    """Set command to move to given coordinates."""
    target_angle = math.atan2(target_y - tank.y,
                    target_x - tank.x)
    relative_angle = normalize_angle(target_angle - tank.angle)
    bzrc.do_commands([Command(tank.index, 1, 2 * relative_angle, False)])

def turnToPosition(bzrc, tank, target_x, target_y):
    """Set command to move to given coordinates."""
    target_angle = math.atan2(target_y - tank.y,
                    target_x - tank.x)
    relative_angle = normalize_angle(target_angle - tank.angle)
    bzrc.do_commands([Command(tank.index, 0, 2 * relative_angle, False)])

def getDistance(p0, p1):
    return math.sqrt((p0.x - p1.x)**2 + (p0.y - p1.y)**2)

def getRandomPoint(target_x, target_y):
    x = 1000
    y = 1000
    while True:
        x = randint(target_x-300, target_x+300)
        y = randint(target_y-300, target_x+300)
        if getDistance(Point(x, y), Point(target_x, target_y)) <= 325:
            return Point(x, y)

def readCommandLine():
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', '-p', required=True, default='localhost', help='Hostname to connect to')
    parser.add_argument('--socket', '-s', required=True, default=0, help='Team socket to connect to')
    parser.add_argument('--log', '-l', required=False, default=False, help='Boolean value for logging or no logging')
    parser.add_argument('--type', '-t', required=True, default=1, help='{1:"sitting duck", 2:"constant x,y", 3:"wild pigeon"')
    return parser.parse_args()

if __name__ == '__main__':
    try:
        args = readCommandLine()
    except:
        print desc
        raise
    hostname = args.host
    socket = int(args.socket)
    if args.log == "True":
        log = True
    else:
        log = False
    bzrc, agent = startRobot(hostname, socket)
    if args.type == '1':
        agent.type1()
    elif args.type == '2':
        agent.type2()
    elif args.type == '3':
        agent.type3()
    else:
        print desc
        raise