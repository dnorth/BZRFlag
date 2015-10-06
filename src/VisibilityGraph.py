from bzrc import BZRC, Command

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    return bzrc

bzrc = startRobot('localhost', 60960)

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

class VisibilityLine():
    def __init__():

def checkIntersection(p1, p2, p3, p4):
    # proper intersection
    

def getPoints(step):
    points = []
    for x in range(-400, 401, step):
        for y in range(-400, 401, step):
            points.append(Point(x, y))
    return points

def VisibilityGraph(bzrc):
    points = getPoints(20)
    s = bzrc.get_obstacles()
