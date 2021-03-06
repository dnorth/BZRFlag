from bzrc import BZRC, Command
import Queue
import math
from time import sleep

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    return bzrc

bzrc = startRobot('localhost', 58096)

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

def getDistanceSoFar(path):
    distance = 0
    for x in range(len(path)-1):
        distance += getDistance(path[x], path[x+1])
    return distance

def aStar(startPoint, endPoint, visDict):
    visited, queue = set([startPoint]), Queue.PriorityQueue()
    path = [startPoint]
    queue.put((getDistance(startPoint, endPoint), path))
    print "Starting"
    while not queue.empty():
        (cost, path) = queue.get()
        last_node = path[-1]
        if last_node == endPoint:
            print "Last Node: x- %s y- %s is equal to End Point: x- %s y- %s" %(last_node.x, last_node.y, endPoint.x, endPoint.y)
            return path
        for node in visDict[last_node]:
            if node not in visited:
                visited.add(node)
                cost = getDistanceSoFar(path + [node]) + getDistance(node, endPoint)
                queue.put((cost, path + [node]))
    print "Ending"

def getNextPoint(path, visDict, currPoint, visited, endPoint):
    potential_points = filter(lambda x : x not in visited, visDict[currPoint])
    if len(potential_points) == 0:
        return False
    for point in potential_points:
        if point == endPoint:
            return path + [endPoint]
        new_path = getNextPoint(path + [point], visDict, point, visited+[point], endPoint)
        if new_path == False:
            continue
        if new_path:
            if endPoint in new_path:
                return new_path

def dfs(startPoint, endPoint, visDict):
    path = [startPoint]
    visited = [startPoint]
    path = getNextPoint(path, visDict, startPoint, visited, endPoint)
    return path

def plotPathToGNU(pointList, title="Plot"):
    f = open('path_plot.gpi','w')
    cost = str(getDistanceSoFar(pointList))
    f.write('set title "{title} (cost={cost})"\n'.format(title=title, cost=cost))
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

def calcCenter(base):
    return (base.corner1_x + base.corner3_x) / 2 , (base.corner1_y + base.corner3_y) / 2

def getBases(bzrc):
    bases = {}
    for base in bzrc.get_bases():
        setattr(base, 'center', calcCenter(base))
        bases[base.color] = base
    return bases

def getTank(bzrc, index):
    return bzrc.get_mytanks()[index]

def followPath(bzrc, tank, path):
    if getDistance(Point(tank.x, tank.y), path[0]) > 100:
        print "Tank is too far from startPoint"
        return
    i = 1
    while True:
        while True:
            tank = getTank(bzrc, tank.index)
            if getDistance(path[i], Point(tank.x, tank.y)) <= 20:
                break
            moveToPosition(bzrc, tank, path[i].x, path[i].y)
        i += 1
        if i >= len(path):
            break
    bzrc.speed(tank.index, 0)
    bzrc.angvel(tank.index, 0)

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

bases = getBases(bzrc)
bluebase = Point(bases['blue'].center[0], bases['blue'].center[1])
redbase = Point(bases['red'].center[0], bases['red'].center[1])

visDict = VisibilityGraph(bzrc, startPoint=bluebase, endPoint=redbase)
bfsPath = bfs(bluebase, redbase, visDict)
dfsPath = dfs(bluebase, redbase, visDict)
aStarPath = aStar(bluebase, redbase, visDict)

tanks = bzrc.get_mytanks()


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




