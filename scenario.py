import modbus_srv

class Scenario(object):

    def __init__(self, mbs: modbus_srv.TestBench):
        self.hard = mbs

    def run(self):
        print(self.hard.MPCH.enabled)


