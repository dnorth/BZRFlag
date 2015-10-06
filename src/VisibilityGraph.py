from bzrc import BZRC, Command

def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    agent = Agent(bzrc)
    return bzrc, agent

def VisibilityGraph(s):
