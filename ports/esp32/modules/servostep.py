
import _servostep as ps
import time
import socket
import uwebsocket
import websocket_helper
import _thread
import ujson

from math import pi
DEGREE = pi/180.0
RPS = 2.0*pi
RPM = RPS/60.0


class Servostep:

    interactiveMode = True


    data_socket_listen = None
    data_socket_client = None
    data_websocket = None


    def __init__(self):
        self._start_data_websocket()
        _thread.start_new_thread(self._thread_send_current_status_to_ws, ())


    def run(self):
        ps.run()
        self._wait_completion()
        #ps.power_off()


    def _thread_send_current_status_to_ws(self):
        while True:
            try:
                time.sleep(0.1)
                if self.data_websocket:
                    while True:
                        log = ps.fetch_log()
                        if log is None:
                            break

                        #self.data_websocket.write('{"t": %d, "cp": %f, "p": %f, "cv": %f, "v": %f}' % log)
                        s = ujson.dumps(log)
                        self.data_websocket.write(s)
            except AttributeError:
                print("WS disappeared")
            except OSError:
                print("WS error during write")
            except KeyboardInterrupt:
                print("KeyboardInterrupt ignored from thread")


    def _start_data_websocket(self):
        PORT = 8080
        print("Websocket on port %d" % PORT)
        self.data_socket_listen = socket.socket()
        self.data_socket_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ai = socket.getaddrinfo("0.0.0.0", PORT)
        addr = ai[0][4]

        self.data_socket_listen.bind(addr)
        self.data_socket_listen.listen(1)
        self.data_socket_listen.setsockopt(socket.SOL_SOCKET, 20, self._accept_conn)

    def _accept_conn(self, socket):
        print("accept_conn")
        client, remote_addr = socket.accept()
        print("\nConnection from:", remote_addr)

        if self.data_websocket:
            print("Closing previous WS")
            self.data_websocket.close()
            self.data_websocket = None

        if self.data_socket_client:
            print("Closing previous socket")
            self.data_socket_client.close()
            self.data_socket_client = None

        self.data_socket_client = client
        websocket_helper.server_handshake(client)
        self.data_websocket = uwebsocket.websocket(self.data_socket_client)
        self.data_socket_client.setblocking(False)


    def _push_cmd(self, cmd):
        print("Pushing %s" % cmd)

        if self.interactiveMode:
            ps.power_off()

        ps.push(
            mode=cmd.mode,
            p=cmd.p,
            v=cmd.v,
            t=cmd.t,
            end_prop=cmd.end.prop if cmd.end else 0,
            end_value=cmd.end.value if cmd.end else None,
            end_comp=cmd.end.comp if cmd.end else 0,
            )

        if self.interactiveMode:
            self.run()

    def _wait_completion(self):
        print("Waiting on queue")
        try:
            while ps.is_running():
                time.sleep(0.1)
        except KeyboardInterrupt:
            ps.power_off()
            raise KeyboardInterrupt
        print("Done")

    def log_reset(self):
        ps.push_log_reset()

    def log_start(self, length=800):
        ps.push_log_start(length)

    def setPosition(self,
                    position=None,
                    max_velocity=1.0*RPS,
                    max_torque=1.0,
                    until_absolute_error_lower_than=None,
                    until_absolute_error_greater_than=None,
                    until_error_lower_than=None,
                    until_error_greater_than=None,
                    until_timeout=None,
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
        elif until_timeout is not None:
            end = EndCondition(ps.END_PROP_TIME, until_timeout, 0)
            

        mode = ps.MODE_POSITION_ABS if position is not None else ps.MODE_POSITION_REL

        if position is None: position = 0.0

        cmd = Command(mode, position, max_velocity, max_torque, end=end)
        self._push_cmd(cmd)
        
        
    def setSpeed(self,
                 velocity,
                 max_torque=1.0,
                 #max_acceleration=10.0,
                 until_position_lower_than=None,
                 until_position_greater_than=None,
                 until_timeout=None,
                 ):
        end = None
        if until_position_lower_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ABS, until_position_lower_than, ps.END_COMP_LT)
        elif until_position_greater_than is not None:
            end = EndCondition(ps.END_PROP_POSITION_ABS, until_position_greater_than, ps.END_COMP_GT)
        elif until_timeout is not None:
            end = EndCondition(ps.END_PROP_TIME, until_timeout, 0)

        cmd = Command(ps.MODE_VELOCITY, None, velocity, max_torque, end=end)
        self._push_cmd(cmd)

    def setTorque(self, t=0):
        cmd = Command(ps.MODE_TORQUE, None, None, t)
        self._push_cmd(cmd)
    

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

class EndCondition:
    
    def __init__(self, prop, value, comp):
        self.prop = prop
        self.value = float(value)
        self.comp = comp
        
    def __repr__(self):
        return "[END: {} {} {}]".format(self.prop, self.comp, self.value)


if __name__ == "__main__":

    from servostep import *
    import _servostep as ps
    m = Servostep()
    m.interactiveMode=False
    ps.set_origin((-417+1)*DEGREE)
    m.setPosition(0, until_absolute_error_lower_than=0.5*DEGREE)
    m.setPosition(0, max_torque=0.20, until_error_greater_than=2*DEGREE)
    m.setPosition(0, max_torque=0.20, until_timeout=0.3)
    m.setPosition(20*DEGREE, max_torque=0.20, max_velocity=0.2*RPS, until_absolute_error_lower_than=0.5*DEGREE)
    m.setSpeed(-5*RPS, until_position_lower_than=9*DEGREE)
    m.setPosition(10*DEGREE, until_timeout=0.1)
    while True:
        m.run()




    ps.getOrigin()
    ps.setOrigin() # sets with current position
    ps.setOrigin(-7.29)

