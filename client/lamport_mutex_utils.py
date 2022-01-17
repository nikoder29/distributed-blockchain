class Timestamp:
    def __init__(self, lamport_clock, pid):
        self.lamport_clock = lamport_clock
        self.pid = pid