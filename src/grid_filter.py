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
THRESHOLD = 0.67
likelihood = {}
prior = {0:0.05, 1:0.95}

desc=''' Example:
    python grid_filter.py -p localhost -s 57413
    '''

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    agent = Agent(bzrc)
    return bzrc, agent

# bzrc = startRobot('localhost', 50719)

grid = None

def draw_grid():
    # This assumes you are using a numpy array for your grid
    width, height = grid.shape
    glRasterPos2f(-1, -1)
    glDrawPixels(width, height, GL_LUMINANCE, GL_FLOAT, grid)
    glFlush()
    glutSwapBuffers()

def update_grid(new_grid):
    global grid
    grid = new_grid

def normalizer(o):
    return likelihood[o,1]*prior[1] + likelihood[o,0]*prior[0]

def bayes(o, s):
    l = likelihood[o,s]
    # print "likelihood is: " + str(l)
    p = prior[s]
    # print "prior is: " + str(p)
    if (l*p)/normalizer(o) >= THRESHOLD:
        #print "THE NUMBER: " + str((l*p)/normalizer(o))
        return 1
    else:
        # print "0 face"
        return 0

def get_bayes_grid(local_grid, position):
    x = position[0]+WIDTH
    y = position[1]+HEIGHT
    x_len = len(local_grid[0])
    y_len = len(local_grid)
    spec_grid = grid[y:y+y_len,x:x+x_len]
    # for x in range(0, len(local_grid)):
    #     for y in range(0, len(local_grid[0])):
    #         spec_grid[x][y] = bayes(local_grid[x][y], spec_grid[x][y])
    new_grid = []
    for a_row, b_row in izip(spec_grid, local_grid):
        new_row = []
        for a_item, b_item in izip(a_row, b_row):
            new_row.append(bayes(a_item, b_item))
        new_grid.append(new_row)
    return new_grid

def update_local_grid(local_grid, position):
    x = position[0]+WIDTH
    y = position[1]+HEIGHT
    x_len = len(local_grid[0])
    y_len = len(local_grid)
    grid[y:y+y_len,x:x+x_len] = local_grid

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
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.tanks = self.bzrc.get_mytanks()
        self.commands = []
        self.time_diff = 0
        self.stop = False
        self.constants = self.bzrc.get_constants()
        likelihood[1,1] = float(self.constants['truepositive']) #truepositive
        likelihood[0,1] = 1 - float(self.constants['truenegative']) #falsenegative
        likelihood[0,0] = float(self.constants['truenegative']) #truenegative
        likelihood[1,0] = 1 - float(self.constants['truepositive']) #falsepositive
        self.moving = False
    def read(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            position, local_grid = self.bzrc.get_occgrid(tank.index)
            rot_grid = numpy.fliplr(numpy.rot90(local_grid, 3))
            bayes_grid = get_bayes_grid(rot_grid, position)
            update_local_grid(bayes_grid, position)
    def update(self):
        self.tanks = self.bzrc.get_mytanks()
    def move(self):
        for tank in filter(lambda x : x.status == 'alive', self.tanks):
            self.commands.append(Command(tank.index, 10, 0.2, False))
        self.bzrc.do_commands(self.commands)
        self.commands = []

def runTimer(bzrc, agent, log=False):
    # start_time = time.time()
    init_window(WIDTH*2,HEIGHT*2)
    while True:
        try:
            # print "update"
            agent.update()
            # print "read"
            agent.read()
            # print "move"
            agent.move()
            # print "draw"
            draw_grid()
        except KeyboardInterrupt:
            print "Exiting due to keyboard interrupt."
            agent.stop = True
            bzrc.close()
            return

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
