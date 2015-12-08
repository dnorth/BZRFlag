from bzrc import BZRC, Command
import math, numpy, argparse
from numpy import dot
from random import randint

desc=''' Example:
    python kalman.py -p localhost -s 57413
    '''

# ---------- Constants

dt = 0.5
c = 0

I = numpy.array([
    [1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 1]
    ])

F = numpy.array([
    [1, dt, (dt*dt)/2, 0, 0, 0],
    [0, 1, dt, 0, 0, 0],
    [0, -c, 1, 0, 0, 0],
    [0, 0, 0, 1, dt, (dt*dt)/2],
    [0, 0, 0, 0, 1, dt],
    [0, 0, 0, 0, -c, 1]
    ])

Ft = numpy.transpose(F)

Sx = numpy.array([
    [0.1, 0, 0, 0, 0, 0],
    [0, 0.1, 0, 0, 0, 0],
    [0, 0, 100, 0, 0, 0],
    [0, 0, 0, 0.1, 0, 0],
    [0, 0, 0, 0, 0.1, 0],
    [0, 0, 0, 0, 0, 100]
    ])

H = numpy.array([
    [1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0]
    ])

Ht = numpy.transpose(H)

sd = 5

Sz = numpy.array([
    [sd*sd, 0],
    [0, sd*sd]
    ])

St = numpy.ones(len(Sx))

mu = [[1],[0],[0],[1],[0],[0]]

z = [[0],[0]]

# ---------- Variables

Xt = numpy.array([
    []
    ])

# ---------- Classes

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
    def _run(self):
        self.is_running = False
        self.start()
        self.update()
        self.evalAndMove()
    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(dt, self._run)
            self._timer.start()
            self.is_running = True
    def stop(self):
        if hasattr(self, '_timer'):
            self._timer.cancel()
        self.is_running = False
    def getXt(self):
        self.update()
        return numpy.array([
                [self.tank.x],
                [0],
                [0],
                [self.tank.y],
                [0],
                [0]
                ])
    # def evalAndMove(self):

    
# ---------- Functions

def calculateKalmanGain():
    part1 = dot(dot(F, St) , Ft) + Sx
    Kt = dot(dot(part1, Ht), pow(dot(dot(H, part1),  Ht) + Sz, -1))
    return Kt

#z represents observed state? [[x], [y]]?
def calculateNewMu(mu, Kt, z):
    mu = dot(F, mu) + dot( Kt,(z - dot(dot(H, F), mu)))
    return mu

def calculateSigmaT(Kt, St):
    St = dot( I - dot(Kt, H), dot(dot(F, St), Ft) + Sx)
    return St

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

def moveToPosition(bzrc, tank, target_x, target_y):
    """Set command to move to given coordinates."""
    target_angle = math.atan2(target_y - tank.y,
                    target_x - tank.x)
    relative_angle = normalize_angle(target_angle - tank.angle)
    bzrc.do_commands([Command(tank.index, 1, 2 * relative_angle, False)])

def facingAngle(tank, target_x, target_y):
    target_angle = math.atan2(target_y - tank.y,
                    target_x - tank.x)
    relative_angle = normalize_angle(target_angle - tank.angle)
    return relative_angle < 0.1

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

def runTimer(bzrc, agent, type, log=False):
    

# ---------- main

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
    runTimer(bzrc, agent, args.type, log)