import sys, argparse, time
from bzrc import BZRC, Command

# --------------------------------- VARIABLES
desc=''' Example:
    python dumb_agent.py -p localhost -s 57413
    '''
# --------------------------------- Agent Object
class Agent(object):
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.time_diff = 0

    def tick(self, time_diff):
        myTanks = self.bzrc.get_mytanks()
        print "Time difference: " + str(time_diff)
        for tank in myTanks:
            #Command takes 4 Parameters- (Tank Index, Speed, Angular Velocity, Whether or not to be shooting)
            command = Command(tank.index, 1, 60, True)
            self.commands.append(command)

        results = self.bzrc.do_commands(self.commands)

# --------------------------------- FUNCTIONS
def startRobot(hostname, socket):
    bzrc = BZRC(hostname, socket)
    agent = Agent(bzrc)
    return bzrc, agent

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

    bzrc, agent = startRobot(hostname, socket)

    prev_time = time.time()


    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()