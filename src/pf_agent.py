import sys, argparse, time
from bzrc import BZRC, Command
from time import sleep
from math import pow, atan2, pi, cos, sin

# --------------------------------- VARIABLES
desc=''' Example:
    python pf_agent.py -p localhost -s 57413
    '''
# --------------------------------- Agent Object
class Agent(object):
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.tanks, self.otherTanks, self.flags, self.shots = self.bzrc.get_lots_o_stuff()
        self.constants = self.bzrc.get_constants()
        self.goals = {}
        self.commands = []
        self.time_diff = 0
        self.shoot_thread = None
        self.stop = False
        self.shoot = False
        self.bases = self.getBases()
        self.color = self.getMyColor()
        self.s = 5
        self.alpha = 5

    def getMyColor(self):
        return self.tanks[0].callsign.split('0')[0]

    def update(self):
        self.tanks, self.otherTanks, self.flags, self.shots = self.bzrc.get_lots_o_stuff()

    def calcCenter(self, base):
        return (base.corner1_x + base.corner3_x) / 2 , (base.corner1_y + base.corner3_y) / 2

    def getBases(self):
        bases = {}
        for base in self.bzrc.get_bases():
            setattr(base, 'center', self.calcCenter(base))
            bases[base.color] = base
        return bases

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * pi * int (angle / (2 * pi))
        if angle <= -pi:
            angle += 2 * pi
        elif angle > pi:
            angle -= 2 * pi
        return angle

    def moveToPosition(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = atan2(target_y - tank.y,
                        target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        self.bzrc.do_commands([Command(tank.index, 1, 2 * relative_angle, True)])
    
    def getGoalDistance(self, tank, x, y):
        x_diff = x - tank.x
        y_diff = tank.y - y
        return pow(pow(x_diff, 2) + pow(y_diff, 2), 0.5)

    def setGoalAngles(self):
        for tank in self.tanks:
            y = self.goals[tank.callsign]['y']
            x = self.goals[tank.callsign]['x']
            self.goals[tank.callsign]['angle'] = atan2(y - tank.y, x - tank.x)

    def setGoalCoords(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            if tank not in self.goals:
                self.goals[tank.callsign] = {}
            t = self.goals[tank.callsign]
            if tank.flag != "-":
                t['x'], t['y'] = self.bases[self.color].center
                t['r'] = 15
                t['distance'] = self.getGoalDistance(tank, t['x'], t['y'])
            else:
                t['x'], t['y'], t['distance'] = self.findClosestFlag(tank)
                t['r'] = 1

    def findClosestFlag(self, tank):
        closestFlag = None
        closestDistance = 10000
        for flag in filter(lambda x: x.poss_color != self.color, self.flags):
            if flag.color == self.color:
                continue
            dist = self.getGoalDistance(tank, flag.x, flag.y)
            if dist < closestDistance:
                closestFlag = flag
                closestDistance = dist
        return closestFlag.x, closestFlag.y, closestDistance

    def seekGoals(self):
        for tank in self.tanks:
            if tank.status == 'alive':
                if tank.callsign in self.goals:
                    x_diff, y_diff = self.seekGoal(tank)
                    self.moveToPosition(tank, tank.x+x_diff, tank.y+y_diff)

    def seekGoal(self, tank):
        x_diff = 0
        y_diff = 0
        g = self.goals[tank.callsign]
        if g['distance'] < g['r']:
            pass
        elif g['r'] <= g['distance'] and g['distance'] <= (self.s + g['r']):
            x_diff = self.aplha * (g['distance'] - g['r']) * cos(g['angle'])
            y_diff = self.aplha * (g['distance'] - g['r']) * sin(g['angle'])
        elif g['distance'] > self.s + g['r']:
            x_diff = self.alpha * self.s * cos(g['angle'])
            y_diff = self.alpha * self.s * sin(g['angle'])
        return x_diff, y_diff

# --------------------------------- FUNCTIONS
def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    agent = Agent(bzrc)
    return bzrc, agent

def runTimer(bzrc, agent, log):
    start_time = time.time()
    while True:
        try:
            agent.update()
            agent.setGoalCoords()
            agent.setGoalAngles()
            agent.seekGoals()
        except KeyboardInterrupt:
            print "Exiting due to keyboard interrupt."
            agent.stop = True
            agent.shoot_thread.join()
            bzrc.close()
            return      

# --------------------------------- MAIN FUNCTION
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

    runTimer(bzrc, agent, log)


