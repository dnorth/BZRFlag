import sys, argparse, time, threading
from bzrc import BZRC, Command
from time import sleep

# --------------------------------- VARIABLES
desc=''' Example:
    python dumb_agent.py -p localhost -s 57413
    '''
# --------------------------------- Agent Object
class Agent(object):
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.tanks = []
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.time_diff = 0
        self.shoot_thread = None
        self.stop = False

    def updateTanks(self):
        self.tanks = self.bzrc.get_mytanks()

    def allGoForward(self):
        self.updateTanks()
        commands = [Command(tank.index, 1, 0, False) for tank in self.tanks]
        results = self.bzrc.do_commands(commands)

    def allTurn(self):
        self.updateTanks()
        commands = [Command(tank.index, 0, 60, False) for tank in self.tanks]
        results = self.bzrc.do_commands(commands)

    def startShooting(self):
        while not self.stop:
            self.updateTanks()
            for tank in self.tanks:
                self.bzrc.shoot(tank)
            sleep(2)

# --------------------------------- FUNCTIONS
def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    agent = Agent(bzrc)
    return bzrc, agent

def runTimer(bzrc, agent, log):
    start_time = time.time()
    # agent.shoot_thread = threading.Thread(target=agent.startShooting)
    # agent.shoot_thread.start()
    while True:
        try:
            if log:
                print "Moving forward, 5 seconds"
            agent.allGoForward()
            sleep(5)
            if log:
                print "Turning 60 degrees"
            agent.allTurn()
            sleep(1)
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
    log = args.log

    bzrc, agent = startRobot(hostname, socket)

    runTimer(bzrc, agent, log)


