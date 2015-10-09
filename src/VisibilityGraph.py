from bzrc import BZRC, Command
import Queue
from math import hypot

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    return bzrc

bzrc = startRobot('localhost', 56327)
bluebase = Point(bases['blue'].center[0], bases['blue'].center[1])
redbase = Point(bases['red'].center[0], bases['red'].center[1])

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __hash__(self):
        return hash((self.x, self.y))
    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

class VisibilityLine():
    def __init__():

def onSegment(p, q, r):
    if (q.x <= max(p.x, r.x) and q.x >= min(p.x, r.x) and q.y <= max(p.y, r.y) and q.y >= min(p.y, r.y)):
        return True
    return False

def orientation(p, q, r):
    val = (q.y-p.y) * (r.x-q.x) - (q.x-p.x) * (r.y-q.y)
    if val == 0:
        return 0
    elif val > 0:
        return 1
    else:
        return 2

def doesIntersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)
    if o1 != o2 and o3 != o4:
        return True
    elif o1 == 0 and onSegment(p1, p2, q1):
        return True
    elif o2 == 0 and onSegment(p1, q2, q1):
        return True
    elif o3 == 0 and onSegment(p2, p1, q2):
        return True
    elif o4 == 0 and onSegment(p2, q1, q2):
        return True
    else:
        return False

def getPoints(step, startPoint, endPoint):
    points = []
    if startPoint:
        points.append(startPoint)
    if endPoint:
        points.append(endPoint)
    for x in range(-400, 401, step):
        for y in range(-400, 401, step):
            points.append(Point(x, y))
    return points

def getObstacles(bzrc):
    l = bzrc.get_obstacles()
    obstacles = []
    for o in l:
        oList = []
        for vertex in o:
            oList.append(Point(vertex[0], vertex[1]))
        obstacles.append(oList)
    return obstacles

def insideObstacle(p, o):
    o_x = [v.x for v in o]
    o_y = [v.y for v in o]
    if p.x <= max(o_x) and p.x >= min(o_x):
        if p.y <= max(o_y) and p.y >= min(o_y):
            return True
    return False

def checkAgainstObstacleEdges(p1, q1, o):
    for x in range(len(o)):
        p2 = o[x]
        if x == len(o) - 1:
            q2 = o[0]
        else:
            q2 = o[x+1]
        if doesIntersect(p1, q1, p2, q2):
            return True
    return False

def intersectsWithObstacle(p1, q1, obstacles):
    for o in obstacles:
        if insideObstacle(p1, o):
            return True
        elif checkAgainstObstacleEdges(p1, q1, o):
            return True
    return False

def VisibilityGraph(bzrc, stepAmount=40, startPoint=None, endPoint=None):
    points = getPoints(stepAmount, startPoint, endPoint)
    obstacles = getObstacles(bzrc)
    segDict = {}
    for point in points:
        for point1 in points:
            if point != point1:
                if not intersectsWithObstacle(point, point1, obstacles):
                    if point not in segDict:
                        segDict[point] = []
                    segDict[point].append(point1)
    return segDict

def plotVisibilityGraphToGNU(segDict):
    f = open('plot.gpi','w')
    f.write('set title "Potential Fields Plot\n')
    f.write('set xrange [-400.0: 400.0]\n')
    f.write('set yrange [-400.0: 400.0]\n')
    f.write('unset key\n')    
    for key, visiblePoints in segDict.items():
        plotToGNU(key, visiblePoints, f)
    f.write('plot \'-\' with lines\n0 0 0 0\ne')
    f.close()


def plotSingleVisibilityToGNU(startingPoint, visiblePoints, f=None):
    if not f:
        f = open('visibile_plot.gpi','w')
        f.write('set title "Potential Fields Plot\n')
        f.write('set xrange [-400.0: 400.0]\n')
        f.write('set yrange [-400.0: 400.0]\n')
        f.write('unset key\n')
        f.write('set size square\n')
    for visiblePoint in visiblePoints:
        f.write('set arrow from %s, %s to %s, %s lt 3\n' % (startingPoint.x, startingPoint.y, visiblePoint.x, visiblePoint.y))
    if not f:
        f.write('plot \'-\' with lines\n0 0 0 0\ne')
        f.close()

def bfs(startPoint, endPoint, visDict):
    visited, queue = set([startPoint]), Queue.Queue()
    path = [startPoint]
    queue.put(path)
    print "Starting"
    while not queue.empty():
        path = queue.get()
        last_node = path[-1]
        if last_node == endPoint:
            print "Last Node: x- %s y- %s is equal to End Point: x- %s y- %s" %(last_node.x, last_node.y, endPoint.x, endPoint.y)
            return path
        for node in visDict[last_node]:
            if node not in visited:
                visited.add(node)
                queue.put(path + [node])
    print "Ending"

def getDistance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def aStar(startPoint, endPoint, visDict):
    visited, queue = set([startPoint]), Queue.PriorityQueue()
    path = [startPoint]
    queue.put(getDistance(startPoint, endPoint), path)
    print "Starting"
    while not queue.empty():
        cost, path = queue.get()
        last_node = path[-1]
        if last_node == endPoint:
            print "Last Node: x- %s y- %s is equal to End Point: x- %s y- %s" %(last_node.x, last_node.y, endPoint.x, endPoint.y)
            return path
        for node in visDict[last_node]:
            if node not in visited:
                visited.add(node)
                queue.put(cost + getDistance(node, endPoint), path + [node])
    print "Ending"

def plotPathToGNU(pointList):
    f = open('path_plot.gpi','w')
    f.write('set title "Potential Fields Plot\n')
    f.write('set xrange [-400.0: 400.0]\n')
    f.write('set yrange [-400.0: 400.0]\n')
    f.write('unset key\n')
    f.write('set size square\n')
    for x in range(len(pointList)):
        if x+1 != len(pointList): 
            currPoint = pointList[x]
            nextPoint = pointList[x+1]
            f.write('set arrow from %s, %s to %s, %s lt 3\n' % (currPoint.x, currPoint.y, nextPoint.x, nextPoint.y))
    f.write('plot \'-\' with lines\n0 0 0 0\ne')
    f.close()

def getBases(bzrc):
    bases = {}
    for base in bzrc.get_bases():
        setattr(base, 'center', calcCenter(base))
        bases[base.color] = base
    return bases

def calcCenter(base):
    return (base.corner1_x + base.corner3_x) / 2 , (base.corner1_y + base.corner3_y) / 2

#def bfs(startPoint, endPoint, visDict):
#    order = []
#    q = Queue()
#    points = visDict.keys()
#    q.put(startPoint)
#    points.remove(startPoint)
#    while not q.empty():
#        point = q.get()
#        order.append(point)
#        remove_points = []
#        for point2 in points:
#            if 




