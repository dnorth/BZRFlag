from bzrc import BZRC, Command
import math, numpy, argparse, time
from numpy import dot
from random import randint
import cv2

desc=''' Example:
    python kalman.py -p localhost -s 57413
    '''

# ---------- Constants

dt = 0.1
c = 0

I = numpy.matrix([
    [1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 1]
    ])

F = numpy.matrix([
    [1, dt, (dt*dt)/2, 0, 0, 0],
    [0, 1, dt, 0, 0, 0],
    [0, -c, 1, 0, 0, 0],
    [0, 0, 0, 1, dt, (dt*dt)/2],
    [0, 0, 0, 0, 1, dt],
    [0, 0, 0, 0, -c, 1]
    ])

Sx = numpy.matrix([
    [0.1, 0, 0, 0, 0, 0],
    [0, 0.1, 0, 0, 0, 0],
    [0, 0, 100, 0, 0, 0],
    [0, 0, 0, 0.1, 0, 0],
    [0, 0, 0, 0, 0.1, 0],
    [0, 0, 0, 0, 0, 100]
    ])

S0 = numpy.matrix([
    [100, 0, 0, 0, 0, 0],
    [0, 0.1, 0, 0, 0, 0],
    [0, 0, 0.1, 0, 0, 0],
    [0, 0, 0, 100, 0, 0],
    [0, 0, 0, 0, 0.1, 0],
    [0, 0, 0, 0, 0, 0.1]
    ])

H = numpy.matrix([
    [1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0]
    ])

sd = 5

Sz = numpy.matrix([
    [sd*sd, 0],
    [0, sd*sd]
    ])

# ---------- Classes

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __hash__(self):
        return hash((self.x, self.y))
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        else:
            return (self.x, self.y) == (other.x, other.y)

class Agent(object):
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.tank = self.bzrc.get_mytanks()[0]
        self.enemy = self.bzrc.get_othertanks()[0]
        self.commands = []
        self.constants = self.bzrc.get_constants()
        self.mu = [[0],[0],[0],[0],[0],[0]]
        self.z = [[0],[0]] #z represents observed state. [[x], [y]]
        self.Kt = 0
        self.St = S0
        self.world = numpy.zeros((800,800,3))
    def tick(self):
        #self.update()
        self.updateEnemyPos()
        self.Kt = calculateKalmanGain(self.St)
        self.mu = calculateNewMu(self.mu, self.Kt, self.z)
        self.St = calculateSigmaT(self.Kt, self.St)
        #print "Kalman Gain: " + str(self.Kt)
        #print "Mu: " + str(self.mu)
        #print "Sigma T: " + str(self.St)
    def update(self):
        self.tank = self.bzrc.get_mytanks()[0]
    def updateEnemyPos(self):
        self.enemy = self.bzrc.get_othertanks()[0]
        self.z = [[self.enemy.x], [self.enemy.y]]
    def plotWorld(self):
        newX = self.getPlotX(self.enemy.x)
        newY = self.getPlotY(self.enemy.y)

        muX = self.getPlotX(int(self.mu[0][0]))
        muY = self.getPlotY(int(self.mu[3][0]))
        self.world[newY, newX] = [0,255,0]
        self.world[muY, muX] = [0, 1, 255]
        cv2.imshow("World", self.world)
        cv2.waitKey(1)
    def getPlotX(self, x):
        return x + 400
    def getPlotY(self, y):
        return 400 - y
    
# ---------- Functions

def calculateKalmanGain(St):
    model_uncertainty = F * St * F.T + Sx
    return model_uncertainty *  H.T * numpy.linalg.inv( H * model_uncertainty * H.T + Sz )

def calculateNewMu(mu, Kt_1, z):
    return F * mu + Kt_1 * (z - H * F * mu)

def calculateSigmaT(Kt, St):
    return (I - Kt * H) * (F * St * F.T + Sx)

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

def runTimer(bzrc, agent, log=False):
    try:
        prev_time = time.time()
        while True:
            time_diff = time.time() - prev_time
            if time_diff >= dt:
                agent.tick()
                agent.plotWorld()
                prev_time = time.time()
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()

# ---------- main

def readCommandLine():
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', '-p', required=True, default='localhost', help='Hostname to connect to')
    parser.add_argument('--socket', '-s', required=True, default=0, help='Team socket to connect to')
    parser.add_argument('--log', '-l', required=False, default=False, help='Boolean value for logging or no logging')
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
    runTimer(bzrc, agent, log=False)