from bzrc import BZRC, Command
import math, numpy
from numpy import dot

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

# ---------- Agent

class Agent(object):
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.tank = self.bzrc.get_mytanks()[0]
        self.commands = []
        self.constants = self.bzrc.get_constants()
        self.is_running=False
    def _run(self):
        self.is_running=False
        self.start()
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
    def evalAndMove(self):

    
# ---------- Functions

def calculateKalmanGain():
    part1 = dot(dot(F, St) , Ft) + Sx
    kT = dot(dot(part1, Ht), pow(dot(dot(H, part1),  Ht) + Sz, -1))
    return kT

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    possibleGoals = getPossibleGoals(50)
    agent = Agent(bzrc, possibleGoals)
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

def runTimer(bzrc, agent, log=False):


# ---------- main

def readCommandLine():
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', '-p', required=True, default='localhost', help='Hostname to connect to')
    parser.add_argument('--socket', '-s', required=True, default=0, help='Team socket to connect to')
    parser.add_argument('--log', '-l', required=False, default=False, help='Boolean value for logging or no logging')
    # parser.add_argument('--plot', required=False, default=False, help='Plot tangential fields')
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
    runTimer(bzrc, agent, log)