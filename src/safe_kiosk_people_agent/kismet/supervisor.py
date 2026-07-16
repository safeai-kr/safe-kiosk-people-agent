from threading import Event
class KismetSupervisor:
    def __init__(self,runner): self.runner=runner
    def run(self,stop:Event)->int: return self.runner.run(stop)
