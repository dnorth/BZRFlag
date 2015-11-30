from bzrc import BZRC, Command
import Queue, argparse, math, numpy
from time import sleep
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros

WIDTH = 400
HEIGHT = 400

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
        # self.bases = self.getBases()
        # self.color = self.getMyColor()
        self.move = {}
    def read(self):
        for tank in filter(lambda x : x.status == 'alive' and x.index == 0, self.tanks):
            position, local_grid = self.bzrc.get_occgrid(tank.index)
            rot_grid = numpy.rot90(local_grid)
            update_local_grid(rot_grid, position)
    def update(self):
        self.tanks = self.bzrc.get_mytanks()
    # def move(self):
        # for tank in 

def runTimer(bzrc, agent, log=False):
    # start_time = time.time()
    init_window(WIDTH*2,HEIGHT*2)
    while True:
        try:
            agent.update()
            agent.read()
            # agent.move()
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
