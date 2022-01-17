from functools import total_ordering

@total_ordering
class Timestamp:
    def __init__(self, lamport_clock, pid):
        self.lamport_clock = lamport_clock
        self.pid = pid
    
    def __lt__(self, obj):
        return ((self.lamport_clock < obj.lamport_clock)\
            or (((self.lamport_clock == obj.lamport_clock) and (self.pid < obj.pid))))

    def __eq__(self, obj):
        return ((self.lamport_clock == obj.lamport_clock)\
            and (self.pid == obj.pid))
  
    def __repr__(self):
        return " ".join(["Lamport Clock:", str(self.lamport_clock), " pid:", str(self.pid)])