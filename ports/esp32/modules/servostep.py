
import _servostep as ps
import time



from math import pi
DEGREE = pi/180.0
RPS = 2.0*pi
RPM = RPS/60.0


class Servostep:

    # MODE = {
    #     'p': _servostep.MODE_POSITION_ABS,
    #     'p_rel': _servostep.MODE_POSITION_REL,
    #     'p_modulo': _servostep.MODE_POSITION_MODULO,
    #     'v': _servostep.MODE_VELOCITY,
    # }

    # END_PROP = {
    #     'time': _servostep.END_PROP_TIME,
    #     'p': _servostep.END_PROP_POSITION_ABS,
    #     'p_rel': _servostep.END_PROP_POSITION_REL,
    #     #'p_modulo': _servostep.END_PROP_POSITION_MODULO,
    #     'v': _servostep.END_PROP_VELOCITY,
    #     't': _servostep.END_PROP_TORQUE,
    # }


    def run(self, arg, wait=True):

        ps.power_off()

        if isinstance(arg, Scenario):
            for cmd in arg:
                self._push_cmd(cmd)
        elif isinstance(arg, Command):
            self._push_cmd(arg)
        else:
            raise ValueError

        ps.run()

        if wait:
            self._wait_empty_queue()
        print("Run done")


    def _push_cmd(self, cmd):
        print("Pushing %s" % cmd)

        ps.push(
            mode=cmd.mode,
            p=cmd.p,
            v=cmd.v,
            t=cmd.t,
            end_prop=cmd.end.prop if cmd.end else None,
            end_value=cmd.end.value if cmd.end else None,
            end_comp=cmd.end.comp if cmd.end else None,
            )


    def _wait_empty_queue(self):
        print("Waiting on queue")
        time.sleep(3)
        print("Done")


    def setPosition(self,
                    position=None,
                    max_velocity=10.0*RPS,
                    max_torque=1.0,
                    until_absolute_error_lower_than=None,
                    until_absolute_error_greater_than=None,
                    until_error_lower_than=None,
                    until_error_greater_than=None,
                    ):

        ps.power_off()

        end = None
        if until_absolute_error_lower_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ABSOLUTE_ERROR, until_absolute_error_lower_than, ps.END_COMP_LT)
        elif until_absolute_error_greater_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ABSOLUTE_ERROR, until_absolute_error_greater_than, ps.END_COMP_GT)
        elif until_error_lower_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ERROR, until_error_lower_than, ps.END_COMP_LT)
        elif until_error_greater_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ERROR, until_error_greater_than, ps.END_COMP_GT)

        mode = ps.MODE_POSITION_ABS if position else ps.MODE_POSITION_REL

        if position is None: position = 0.0

        cmd = Command(mode, position, max_velocity, max_torque, end=end)

        self._push_cmd(cmd)
        ps.run()
        

    def setSpeed(self,
                 speed=None,
                 max_torque=1.0,
                 until_position_lower_than=None,
                 until_position_greater_than=None,):
        pass



class Scenario(list):
    loop = 0

    def __str__(self):
        items = "\n".join([str(i) for i in self])
        return "SCENARIO loop={} wait={}\n{}".format(self.loop, self.wait, items)
    

class Command:

    def __init__(self, mode, p=None, v=None, t=None, end=None):
        self.mode = mode
        #assert(self.mode in [_servostep.MODE_POSITION_ABS'p', 'v'])
        self.p = float(p) if p is not None else None
        self.v = float(v) if v is not None else None
        self.t = float(t) if t is not None else None
        self.end = end
        assert(isinstance(self.end, EndCondition))

    def __repr__(self):
        return "[CMD mode={} p={} v={} t={} end={}]".format(self.mode, self.p, self.v, self.t, self.end)

#Command2('v', p=0, v=10, end=EndCondition("time", 1))


class EndCondition:
    
    def __init__(self, prop, value, comp):
        self.prop = prop
        self.value = float(value)
        self.comp = comp
        #assert(prop in ['time', 'position', 'speed', 'torque'])
        #assert(comparison in ['<=', '>='])

    def __repr__(self):
        #return "[END: {0.prop} {0.comparison} {0.value}]".format(self)
        return "[END: {} {} {}]".format(self.prop, self.comp, self.value)


if __name__ == "__main__":

    s1 = Scenario([
            Command('p', 5, end=True),
            Command('v', 50, end=EndCondition("position", 5, ">=")),
         ])

    s1.loop = 2

    m = Servostep()
    m.run(s1)

    m.run(Scenario([Command('v', p=0, v=10, end=EndCondition("time", 0.1)),]))



    from servostep import *
    m = Servostep()
    m.setPosition(300*DEGREE, until_absolute_error_lower_than=0.5*DEGREE)
    



    m = Servostep()
    while True:

        #m.setInteractiveMode()
        #m.setScenarioMode()

        # Go to idle position and wait it is reached within 0.5 degree
        m.setPosition(300*DEGREE, until_absolute_error_lower_than=0.5*DEGREE)
        
        # Lower the torque to 5% and wait for a -2 degrees disturbance
        m.setPosition(max_torque=0.05, until_error_lower_than=-2*DEGREE)
        
        # An object moved the rotor by more than 2 degrees, starting the catapult cycle!

        # Set a high negative speed until a -30 degree position
        m.setSpeed(-1200*RPM, until_position_lower_than=270*DEGREE)

        # Set a high positive speed until a +15 degree position
        m.setSpeed(1200*RPM, until_position_greater_than=315*DEGREE)

        # Go back to idle position
        m.setPosition(300*DEGREE, until_absolute_error_lower_than=0.5*DEGREE)

        m.runScenario()





