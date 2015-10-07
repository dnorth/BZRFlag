from bzrc import BZRC, Command

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    return bzrc

bzrc = startRobot('localhost', 56327)

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

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

def getPoints(step):
    points = []
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
    o_y = [v.x for v in o]
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

def VisibilityGraph(bzrc):
    points = getPoints(20)
    obstacles = getObstacles(bzrc)
    segDict = {}
    for point in points:
        for point1 in points:
            if point != point1:
                if not intersectsWithObstacle(point, point1, obstacles):
                    if [point.x, point.y] not in segDict:
                        segDict[point.x, point.y] = []
                    segDict[point.x, point.y].append(point1)
    return segDict


def plotToGNU(startingPoint, visiblePoints):
    f = open('plot.gpi','w')
    f.write('set title "Potential Fields Plot\n')
    f.write('set xrange [-400.0: 400.0]\n')
    f.write('set yrange [-400.0: 400.0]\n')
    f.write('unset key\n')
    f.write('set size square\n')
    for visiblePoint in visiblePoints:
        f.write('set arrow from %s, %s to %s, %s lt 3\n' % (startingPoint.x, startingPoint.y, visiblePoint.x, visiblePoint.y))
    f.write('plot \'-\' with lines\n0 0 0 0\ne')
    f.close()

def bfs(startPoint, endPoint, visDict):
    order = []
    q = Queue()
    points = visDict.keys()
    q.put(startPoint)
    points.remove(startPoint)
    while not q.empty():
        point = q.get()
        order.append(point)
        remove_points = []
        for point2 in points:
            if 




