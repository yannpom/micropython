
import _servostep as ps
import time



from math import pi
DEGREE = pi/180.0
RPS = 2.0*pi
RPM = RPS/60.0


class Servostep:

    interactiveMode = True


    def run(self):
        ps.run()
        self._wait_completion()
        ps.power_off()

    def _push_cmd(self, cmd):
        print("Pushing %s" % cmd)

        if self.interactiveMode:
            ps.power_off()

        ps.push(
            mode=cmd.mode,
            p=cmd.p,
            v=cmd.v,
            t=cmd.t,
            end_prop=cmd.end.prop if cmd.end else None,
            end_value=cmd.end.value if cmd.end else None,
            end_comp=cmd.end.comp if cmd.end else None,
            )

        if self.interactiveMode:
            ps.run()
            self._wait_completion()
            ps.power_off()


    def _wait_completion(self):
        print("Waiting on queue")
        try:
            while ps.is_running():
                time.sleep(0.01)
        except KeyboardInterrupt:
            ps.power_off()
            raise KeyboardInterrupt
        print("Done")


    def setPosition(self,
                    position=None,
                    max_velocity=1.0*RPS,
                    max_torque=1.0,
                    until_absolute_error_lower_than=None,
                    until_absolute_error_greater_than=None,
                    until_error_lower_than=None,
                    until_error_greater_than=None,
                    ):

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
        
        
    def setSpeed(self,
                 velocity,
                 max_torque=1.0,
                 until_position_lower_than=None,
                 until_position_greater_than=None,):
        end = None
        if until_position_lower_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ABS, until_position_lower_than, ps.END_COMP_LT)
        elif until_position_greater_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ABS, until_position_greater_than, ps.END_COMP_GT)
        
        cmd = Command(ps.MODE_VELOCITY, None, velocity, max_torque, end=end)
        self._push_cmd(cmd)


# class Scenario(list):
#     loop = 0

#     def __str__(self):
#         items = "\n".join([str(i) for i in self])
#         return "SCENARIO loop={} wait={}\n{}".format(self.loop, self.wait, items)
    

class Command:

    def __init__(self, mode, p=None, v=None, t=None, end=None):
        self.mode = mode
        #assert(self.mode in [_servostep.MODE_POSITION_ABS'p', 'v'])
        self.p = float(p) if p is not None else None
        self.v = float(v) if v is not None else None
        self.t = float(t) if t is not None else None
        self.end = end
        assert(isinstance(self.end, EndCondition) or end is None)

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

    # s1 = Scenario([
    #         Command('p', 5, end=True),
    #         Command('v', 50, end=EndCondition("position", 5, ">=")),
    #      ])

    # s1.loop = 2

    # m = Servostep()
    # m.run(s1)

    # m.run(Scenario([Command('v', p=0, v=10, end=EndCondition("time", 0.1)),]))



    from servostep import *
    m = Servostep()
    m.setPosition(300*DEGREE, until_absolute_error_lower_than=0.5*DEGREE)
    



    m = Servostep()
    while True:

        m.interactiveMode = True
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






