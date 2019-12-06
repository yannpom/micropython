
import _servostep
import time


class Servostep:

    MODE = {
        'p': _servostep.MODE_POSITION_ABS,
        'p_rel': _servostep.MODE_POSITION_REL,
        'p_modulo': _servostep.MODE_POSITION_MODULO,
        'v': _servostep.MODE_VELOCITY,
    }

    END_PROP = {
        'time': _servostep.END_PROP_TIME,
        'p': _servostep.END_PROP_POSITION_ABS,
        'p_rel': _servostep.END_PROP_POSITION_REL,
        'p_modulo': _servostep.END_PROP_POSITION_MODULO,
        'v': _servostep.END_PROP_VELOCITY,
        't': _servostep.END_PROP_TORQUE,
    }


    def run(self, arg, wait=True):

        _servostep.power_off()

        if isinstance(arg, Scenario):
            for cmd in arg:
                self._push_cmd(cmd)
        elif isinstance(arg, Command):
            self._push_cmd(arg)
        else:
            raise ValueError

        _servostep.run()

        if wait:
            self._wait_empty_queue()
        print("Run done")



    def _push_cmd(self, cmd):
        print("Pushing %s" % cmd)

        _servostep.push(
            mode=self.MODE[cmd.mode],
            p=cmd.p,
            v=cmd.v,
            end_prop=self.END_PROP[cmd.end.prop] if cmd.end else None,
            end_value=cmd.end.value if cmd.end else None,
            )


    def _wait_empty_queue(self):
        print("Waiting on queue")
        time.sleep(3)
        print("Done")



class Scenario(list):
    loop = 0

    def __str__(self):
        items = "\n".join([str(i) for i in self])
        return "SCENARIO loop={} wait={}\n{}".format(self.loop, self.wait, items)
    

class Command:

    def __init__(self, mode, p=None, v=None, p_bounds=None, v_max=60.0, a_max=60.0, t_max=1.0, end=None):
        self.mode = mode
        assert(self.mode in ['p', 'v'])
        self.p = float(p) if p is not None else None
        self.v = float(v) if v is not None else None
        #self.p_bounds = len(p_bounds)[float(i) for i in p_bounds]
        #self.v_max = v_max
        #self.a_max = a_max
        #self.t_max = t_max
        self.end = end
        assert(isinstance(self.end, EndCondition) or end is True)

    def __repr__(self):
        #return "[CMD mode={0.mode} p={0.p} v={0.v} end={0.end}]".format(self)
        return "[CMD mode={} p={} v={} end={}]".format(self.mode, self.p, self.v, self.end)

#Command2('v', p=0, v=10, end=EndCondition("time", 1))


class EndCondition:
    
    def __init__(self, prop, value, comparison=">="):
        self.prop = prop
        self.value = float(value)
        self.comparison = comparison
        assert(prop in ['time', 'position', 'speed', 'torque'])
        assert(comparison in ['<=', '>='])

    def __str__(self):
        #return "[END: {0.prop} {0.comparison} {0.value}]".format(self)
        return "[END: {} {} {}]".format(self.prop, self.comparison, self.value)


if __name__ == "__main__":

    s1 = Scenario([
            Command('p', 5, end=True),
            Command('v', 50, end=EndCondition("position", 5, ">=")),
         ])

    s1.loop = 2

    m = Servostep()
    m.run(s1)

    from servostep import *
    m = Servostep()
    m.run(Scenario([Command('v', p=0, v=10, end=EndCondition("time", 0.1)),]))

