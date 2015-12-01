from bzrc import BZRC, Command
import Queue, argparse, math, numpy
from time import sleep
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros
from itertools import izip

WIDTH = 400
HEIGHT = 400
THRESHOLD = 0.9
likelihood = {}
# prior = {1:0.5, 0:0.5}
prior = numpy.empty([800,800])
prior.fill(0.5)


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visited = False
    def __hash__(self):
        return hash((self.x, self.y))
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        else:
            return (self.x, self.y) == (other.x, other.y)

desc=''' Example:
    python grid_filter.py -p localhost -s 57413
    '''

def getPossibleGoals(step):
    possibleGoals = []
    for x in range(-400, 401, step):
        for y in range(-400, 401, step):
            possibleGoals.append(Point(x, y))
    return possibleGoals

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    possibleGoals = getPossibleGoals(50)
    agent = Agent(bzrc, possibleGoals)
    return bzrc, agent

grid = None

def draw_grid():
    # This assumes you are using a numpy array for your grid
    width, height = grid.shape
    glRasterPos2f(-1, -1)
    glDrawPixels(width, height, GL_LUMINANCE, GL_FLOAT, grid)
    glFlush()
    glutSwapBuffers()

def update_grid():
    global grid
    grid = prior

def bayes(o, x, y):
    if o == 1:
        bel_occ = likelihood['truepositive'] * prior[x][y]
        bel_unocc =  likelihood['falsenegative'] * (1-prior[x][y])
    else:
        bel_occ = likelihood['falsepositive'] * prior[x][y]
        bel_unocc =  likelihood['truenegative'] * (1-prior[x][y])

    posterior = (bel_occ)/(bel_occ + bel_unocc)
    prior[x][y] = posterior

def get_bayes_grid(local_grid, position):
    x_pos = position[0]+WIDTH
    y_pos = position[1]+HEIGHT
    for x in range(0, len(local_grid)):
        for y in range(0, len(local_grid[0])):
            bayes(local_grid[x][y], y+y_pos, x+x_pos) #y is opposite of what we expect

def init_window(width, height):
    global window
    global grid
    grid = zeros((width, height))
    glutInit(())
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(0, 0)
    window = glutCreateWindow("Grid filter")
    glutDisplayFunc(draw_grid)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

class Agent(object):
    def __init__(self, bzrc, possibleGoals):
        self.bzrc = bzrc
        self.possibleGoals = possibleGoals
        self.tanks = self.bzrc.get_mytanks()
        self.commands = []
        self.time_diff = 0
        self.stop = False
        self.constants = self.bzrc.get_constants()
        self.goals = {}
        likelihood['truepositive'] = float(self.constants['truepositive']) #truepositive
        likelihood['falsenegative'] = 1 - float(self.constants['truenegative']) #falsenegative
        likelihood['truenegative'] = float(self.constants['truenegative']) #truenegative
        likelihood['falsepositive'] = 1 - float(self.constants['truepositive']) #falsepositive
        self.moving = False
    def read(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            position, local_grid = self.bzrc.get_occgrid(tank.index)
            bayes_grid = get_bayes_grid(local_grid, position)
            update_grid()
    def update(self):
        self.tanks = self.bzrc.get_mytanks()
    def move(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            g = self.goals[tank.callsign]
            if(g == "Done"):
                elf.commands.append(Command(tank.index, 0, 0, False))
                self.bzrc.do_commands(self.commands)
                self.commands = []
            elif(g == None):
                print "uh oh"
                pass
            else:
                moveToPosition(self.bzrc, tank, g.x, g.y) 
    def setGoalInfo(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            if tank.callsign not in self.goals:
                self.goals[tank.callsign] = None
            g = self.goals[tank.callsign]
            if g == None:
                self.goals[tank.callsign] = safe_list_get([x for x in self.possibleGoals if x.visited == False and x not in self.goals.values()], 0)
                if isinstance(self.goals[tank.callsign], Point):
                    print "New goal: X:" + str(self.goals[tank.callsign].y) + " Y: " + str(self.goals[tank.callsign].y)
                else:
                    print "No More Goals."
            elif g == "Done":
                continue
            elif getDistance(g, Point(tank.x, tank.y)) <= 50:
                print "I'm by my goal!"
                print self.possibleGoals[self.possibleGoals.index(self.goals[tank.callsign])].visited
                self.possibleGoals[self.possibleGoals.index(self.goals[tank.callsign])].visited = True
                self.goals[tank.callsign] = None
def getDistance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def safe_list_get (l, idx):
  try:
    return l[idx]
  except IndexError:
    return "Done"

def runTimer(bzrc, agent, log=False):
    # start_time = time.time()
    init_window(WIDTH*2,HEIGHT*2)
    while True:
        try:
            agent.update()
            agent.read()
            agent.setGoalInfo()
            agent.move()
            draw_grid()
        except KeyboardInterrupt:
            print "Exiting due to keyboard interrupt."
            agent.stop = True
            bzrc.close()
            return

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
