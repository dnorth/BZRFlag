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
        self.alpha, self.beta = 5, 10
        self.OBSTACLE_RADIUS = 2
        self.s_obstacles = self.getObstacles()
        self.d_obstacles = {}
        self.move = {}

    def getMyColor(self):
        return self.tanks[0].callsign.split('0')[0]

    def update(self):
        self.tanks, self.otherTanks, self.flags, self.shots = self.bzrc.get_lots_o_stuff()

    def calcCenter(self, base):
        return (base.corner1_x + base.corner3_x) / 2 , (base.corner1_y + base.corner3_y) / 2

    def getObstacles(self):
        n = 0
        obstacles = {}
        for obstacle in self.bzrc.get_obstacles():
            obstacles[n] = {}
            obstacles[n]['x'] = (obstacle[0][0] + obstacle[2][0]) / 2
            obstacles[n]['y'] = (obstacle[0][1] + obstacle[2][1]) / 2
            obstacles[n]['r'] = self.getDistance(obstacles[n]['x'], obstacles[n]['y'], obstacle[0][0], obstacle[0][1]) * self.OBSTACLE_RADIUS
            n +=1
        return obstacles

        # n = 0
        # obstacles = {}
        # for obstacle in self.bzrc.get_obstacles():
        #     for x in range(len(obstacle)):
        #         obstacles[n] = {}
        #         obstacles[n]['x'] = obstacle[x][0]
        #         obstacles[n]['y'] = obstacle[x][1]
        #         next = x+1
        #         if next >= len(obstacle):
        #             next = 0
        #         dist = self.getDistance(obstacle[x][0], obstacle[x][1], obstacle[next][0], obstacle[next][1])
        #         obstacles[n]['r'] = dist * 0.25
        #         n += 1
        # # print obstacles
        # return obstacles

    def getTankFromCallsign(self, callsign):
        return filter(lambda x : x.callsign == callsign, self.tanks)[0]

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
    
    def getDistance(self, x_1, y_1, x_2, y_2):
        x_diff = x_1 - x_2
        y_diff = y_1 - y_2
        return pow(pow(x_diff, 2) + pow(y_diff, 2), 0.5)

    def getTankDistance(self, tank, x, y):
        x_diff = x - tank.x
        y_diff = tank.y - y
        return pow(pow(x_diff, 2) + pow(y_diff, 2), 0.5)

    def getTankAngle(self, tank, x, y):
        return atan2(y - tank.y, x - tank.x)

    def setGoalInfo(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            if tank.callsign not in self.goals:
                self.goals[tank.callsign] = {}
            t = self.goals[tank.callsign]
            if tank.flag != "-":
                t['x'], t['y'] = self.bases[self.color].center
                t['r'] = 15
                t['distance'] = self.getTankDistance(tank, t['x'], t['y'])
            else:
                t['x'], t['y'], t['distance'] = self.findClosestFlag(tank)
                t['r'] = 1
            t['angle'] = self.getTankAngle(tank, t['x'], t['y'])

    def findClosestFlag(self, tank):
        closestFlag = None
        closestDistance = 10000
        for flag in filter(lambda x: x.poss_color != self.color, self.flags):
            if flag.color == self.color:
                continue
            dist = self.getTankDistance(tank, flag.x, flag.y)
            if dist < closestDistance:
                closestFlag = flag
                closestDistance = dist
        if not closestFlag:
            return 0, 0, self.getTankDistance(tank, 0, 0)
        return closestFlag.x, closestFlag.y, closestDistance

    def seekGoals(self):
        for tank in self.tanks:
            if tank.status == 'alive':
                if tank.callsign in self.goals:
                    self.move[tank.callsign] = list(self.seekGoal(tank))

    def seekGoal(self, tank):
        x_diff = 0
        y_diff = 0
        g = self.goals[tank.callsign]
        if g['distance'] < g['r']:
            pass
        elif g['r'] <= g['distance'] and g['distance'] <= (self.s + g['r']):
            x_diff = self.alpha * (g['distance'] - g['r']) * cos(g['angle'])
            y_diff = self.alpha * (g['distance'] - g['r']) * sin(g['angle'])
        elif g['distance'] > self.s + g['r']:
            x_diff = self.alpha * self.s * cos(g['angle'])
            y_diff = self.alpha * self.s * sin(g['angle'])
        return x_diff, y_diff

    def setObstacleInfo(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            if tank.callsign not in self.d_obstacles:
                self.d_obstacles[tank.callsign] = {}
            t = self.d_obstacles[tank.callsign]
            for obstacle in self.s_obstacles:
                t[obstacle] = {}
                t[obstacle]['distance'] = self.getTankDistance(tank, self.s_obstacles[obstacle]['x'], self.s_obstacles[obstacle]['y'])
                t[obstacle]['angle'] = self.getTankAngle(tank, self.s_obstacles[obstacle]['x'], self.s_obstacles[obstacle]['y'])
                t[obstacle]['r'] = self.s_obstacles[obstacle]['r']

    def avoidObstacles(self):
        for tank in self.tanks:
            if tank.status == 'alive':
                if tank.callsign in self.d_obstacles:
                    x_diff, y_diff = self.avoidObstacle(tank)
                    self.move[tank.callsign][0] += x_diff
                    self.move[tank.callsign][1] += y_diff

    def avoidObstacle(self, tank):
        x_diff = 0
        y_diff = 0
        for obstacle, o in self.d_obstacles[tank.callsign].items():
            if o['distance'] < o['r']:
                if o['distance'] != 0:
                    x_diff += -500 * cos(o['angle']) * (1 / o['distance'])
                    y_diff += -500 * sin(o['angle']) * (1 / o['distance'])
            elif o['r'] <= o['distance'] and o['distance'] <= self.s + o['r']:
                x_diff += -1 * self.beta * (self.s + o['r'] - o['distance']) * cos(o['angle'])
                y_diff += -1 * self.beta * (self.s + o['r'] - o['distance']) * sin(o['angle'])
            elif o['distance'] > self.s + o['r']:
                continue
        return x_diff, y_diff

    def moveTanks(self):
        for callsign, m in self.move.items():
            tank = self.getTankFromCallsign(callsign)
            self.moveToPosition(tank, tank.x+m[0], tank.y+m[1])

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
            agent.setGoalInfo()
            agent.setObstacleInfo()
            agent.seekGoals()
            agent.avoidObstacles()
            agent.moveTanks()
        except KeyboardInterrupt:
            print "Exiting due to keyboard interrupt."
            agent.stop = True
            bzrc.close()
            return      

def plotToGNU(bzrc, agent):
    f = open('plot.gpi','w')
    f.write('set title "Potential Fields Plot\n')
    f.write('set xrange [-400.0: 400.0]\n')
    f.write('set yrange [-400.0: 400.0]\n')
    f.write('unset key\n')
    f.write('set size square\n')

    agent.update()
    agent.setGoalInfo()
    agent.setObstacleInfo()
    fakeTank = agent.tanks[0]
    x = -400
    while x < 400:
        fakeTank.x = x
        y = -400
        while y < 400:
            fakeTank.y = y
            agent.setGoalInfo()
            agent.setObstacleInfo()
            x_diff, y_diff = agent.avoidObstacle(fakeTank)
            f.write('set arrow from %s, %s to %s, %s lt 3\n' % (fakeTank.x, fakeTank.y, fakeTank.x + x_diff, fakeTank.y + y_diff))
            x_diff, y_diff = agent.seekGoal(fakeTank)
            f.write('set arrow from %s, %s to %s, %s lt 3\n' % (fakeTank.x, fakeTank.y, fakeTank.x + x_diff, fakeTank.y + y_diff))
            y+= 25
        x += 25


    f.write('plot \'-\' with lines\n0 0 0 0\ne')
    f.close()

# --------------------------------- MAIN FUNCTION
def readCommandLine():
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', '-p', required=True, default='localhost', help='Hostname to connect to')
    parser.add_argument('--socket', '-s', required=True, default=0, help='Team socket to connect to')
    parser.add_argument('--log', '-l', required=False, default=False, help='Boolean value for logging or no logging')
    parser.add_argument('--plot', required=False, default=False, help='Plot tangential fields')
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

    if not args.plot:
        runTimer(bzrc, agent, log)
    else:
        plotToGNU(bzrc, agent)


