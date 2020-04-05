import sys
#import termios

import serial.tools.list_ports
import minimalmodbus
import struct
from collections import deque
from datetime import time, datetime
import copy
import serial as serialutil


class Server(object):
    class ServerError(Exception):
        pass

    def __init__(self):
        self.consol = {"connect": self.connect, "read": self.read_register,
                       "read_scope": self.read_scope, "devices": self.list_devices,
                       "rm": self.rm_device, "write": self.write_register, "close": self.con_close
                       }
        self.devices = []
        self.brake_request = False


    class Device:

        def __init__(self, device, slave_name):
            self.device = device
            self.slave_name = slave_name
            self.holdings = []
            self.inputs = []
            self.scope_maxlen = 10000
            self.scope_fifo = [deque([0] * self.scope_maxlen, maxlen=self.scope_maxlen) for i in range(4)]
            self.scope_timeline = deque([0] * self.scope_maxlen, maxlen=self.scope_maxlen)


    def help(self):
        print("connect [Port Name] [Port Speed] [Device address] [-a] \n "
              "-a all devices, if not define function stop a first device \n")
        print("read_scope [device ID] \n")
        print("read  [device ID] [register number] [register type] \n")
        print("devices \n")
        print("rm [options] [ID]\n"
              "-a clear list of devices, -o remove other devices ")

    def rm_device(self, args):
        """
        rm_device [device ID] [option]
        :param args:
            -a all
            -o remove all except device ID
        :return:
        """
        if len(self.devices) == 0: return
        did = 0
        onlyotion = False
        alloption = False
        try:
            did = int(args[1])
            if did >= len(self.devices): return False
            if did < -1: return False
        except IndexError:
            pass
        except ValueError:
            if args[1] == "-a": alloption = True
            if args[1] == "-o": onlyotion = True
        try:
            if args[2] == "-a": alloption = True
            if args[2] == "-o": onlyotion = True
        except IndexError:
            pass

        if alloption:
            self.devices.clear()
            return True
        if onlyotion:
            tmp = self.devices[did]
            self.devices.clear()
            self.devices.append(tmp)
            return True
        self.devices.pop(did)
        return True

    def list_devices(self, args):
        i = 0
        if len(self.devices) == 0: print("no device connected")
        for el in self.devices:
            print("[", i, "]", el.slave_name, el.device.serial.port, el.device.serial.baudrate, el.device.address)
            print(id(el.device.serial.port))
            i += 1

    def read_scope(self, args):
        """
        read_scope [device ID]
        Read scope device FIFO
        :param args:
            args[1] - device number
        :return:
        """

        curdev = 0
        try:
            curdev = int(args[1])
        except (ValueError, IndexError):
            pass
        if (curdev + 1) > len(self.devices):
            raise self.ServerError("Select another device. Available ", len(self.devices))

        while True:
            try:
                buf = bytearray(map(ord, self.devices[curdev].device._perform_command(20, '\x01\x01\x01')))
                fifo = buf.pop()
                if fifo == 6: print("Scope FIFO overload")
                chnum = buf.pop()
                period = buf.pop()
                buf = struct.unpack('>' + 'h' * (len(buf) // 2), buf)

                if chnum != len(self.devices[curdev].scope_fifo):
                    self.devices[curdev].scope_fifo.clear()
                    self.devices[curdev].scope_fifo = [
                        deque([0] * self.devices[curdev].scope_maxlen,
                              maxlen=self.devices[curdev].scope_maxlen) for i in range(chnum)]
                    self.devices[curdev].scope_timeline = deque(
                        [0] * self.devices[curdev].scope_maxlen,
                        maxlen=self.devices[curdev].scope_maxlen)

                for i in range(chnum):
                    self.devices[curdev].scope_fifo[i].extend(buf[i::chnum])

                t0 = self.devices[curdev].scope_timeline[-1]

                rng = range(0, self.devices[curdev].scope_maxlen)
                rng = map(lambda x: t0+x*period*0.001, rng)
                self.devices[curdev].scope_timeline.extend(rng)
            except (minimalmodbus.SlaveDeviceBusyError, minimalmodbus.InvalidResponseError): return True

    def read_register(self, args):
        """
        read_register  [device ID] [register number] [register type]

        :param args:
            device ID - default 0
            register number - if defined read one register else read all
            register type = 3 -Input , 4 - holding
        :return:
        """
        curdev = 0
        register_to_read = 0
        function_code = 4

        if len(self.devices) == 0: raise self.ServerError("Device not found")
        try:
            curdev = int(args[1])
        except (ValueError, IndexError): pass
        try:
            register_to_read = int(args[2])
        except (ValueError, IndexError): pass

        try:
            function_code = int(args[3])
        except (ValueError, IndexError): pass

        #print(args) # console out

        if (curdev+1) > len(self.devices):
            raise self.ServerError("Select another device. Available ", len(self.devices))

        # device register list initialization
        if (len(self.devices[curdev].inputs) == 0) | (len(self.devices[curdev].holdings) == 0):
            tmp = self.devices[curdev].device.read_registers(0, 2, functioncode=4)
            self.devices[curdev].inputs = [0] * tmp[0]
            self.devices[curdev].holdings = [0] * tmp[1]

        buff = {4: self.devices[curdev].inputs, 3: self.devices[curdev].holdings}

        # read all register
        if register_to_read == 0:
            if function_code == 4:
                self.devices[curdev].inputs = self.devices[curdev].device.read_registers(
                    0,
                    len(self.devices[curdev].inputs),
                    functioncode=function_code)
            if function_code == 3:
                self.devices[curdev].holdings = self.devices[curdev].device.read_registers(
                    0,
                    len(self.devices[curdev].holdings),
                    functioncode=function_code)
        # read one register
        else:
            if register_to_read+1 > len(buff[function_code]): raise ValueError("Input register out of range  ")
            res = buff[function_code][register_to_read] = self.devices[curdev].device.read_registers(
                register_to_read,
                1,
                functioncode=function_code)[0]
            print(args) # console out
            print("  =",res)
        return True

    def write_register(self, args):
        """
                read_register  [device ID] [register number] [value]

                :param args:
                    device ID - default 0
                    register number - if defined read one register else read all
                    register type = 3 -Input , 4 - holding
                :return:
                """
        curdev = 0
        addres = 0
        value = 0

        try:
            curdev = int(args[1])
            addres = int(args[2])
            value = int(args[3])
        except (ValueError, IndexError):
            return False
        if curdev > len(self.devices)-1: return False
        print(args)
        signed = False
        if value < 0: signed = True
        res = self.devices[curdev].device.write_register(addres, value, signed = signed)
        req = "read "+str(curdev)+" "+str(addres)+" 3"
        #print("  =",res)
        #self.main(inpt=req)


    def create_server(self, port, speed, sid):
        """
        Creating Modbus serer and asking devise ID
        :param port: COM port name
        :param speed: COM port baud rate
        :param sid: Modbus slave address
        :param -a: find all devices or stop at first
        :return: True if device found
        """
        master = minimalmodbus.Instrument(port, sid)
        master.serial.close()
        master.serial = serialutil.Serial(port)
        master.serial.baudrate = speed
        master.serial.bytesize = 8
        master.serial.parity = serial.PARITY_NONE
        master.serial.stopbits = 1
        master.serial.timeout = 0.50  # seconds
        master.debug = False
        master.close_port_after_each_call = False
        try:
            print("req id")
            req = master._perform_command(43, '\x0E\x01\x01\x00\x00')
        except (
            ValueError,
            minimalmodbus.NoResponseError,
            minimalmodbus.InvalidResponseError
        ) as e:
            print(e)
            master.serial.close()
            print("port closed")
            return False

        req = req[8:16] + req[32:40] + req[44:52]
        tmp = self.Device(master, req)

        self.devices.append(tmp)
        print("Device ID: ", req)
        return True

    def con_close(self, args):
        if len(self.devices) == 0: return
        for dev in self.devices: dev.device.serial.close
        self.devices = []

    def connect(self, args):
        """
        Server.connect - searching devices

        :param args: connect [Port Name] [Port Speed] [Device address] [-a]
        :return: True/False
        """
        self.devices = []
        serials = serial.tools.list_ports.comports()
        ports = [el.device for el in serials]
        sids = range(1, 5)
        alloption = False
        srcoption = False
        try:
            sids = range(int(args[3]), int(args[3]) + 1)
        except (ValueError, IndexError):
            pass
        try:
            speeds = [int(args[2])]
        except (ValueError, IndexError):
            speeds = [9600, 38400, 115200, 230400, 480000]
        try:
            if args[1] in ports: ports = [args[1]]
        except IndexError:
            pass
        try:
            if args[4] == '-a': alloption = True
            if args[4] == '-s': srcoption = True
        except IndexError:
            pass
        self.brake_request = False

        for port in ports:
            if (alloption is False) & (len(self.devices) != 0): break
            try:
                for sid in sids:
                    if (alloption is False) & (len(self.devices) != 0): break
                    for speed in speeds:
                        if (alloption is False) & (len(self.devices) != 0): break
                        print("Searching:\n  Port =", port, "\n  Speed =", speed, "\n  Modbus ID =", sid)
                        try:
                            self.create_server(port, speed, sid)
                            if self.brake_request: return False
                           # if not self.create_server(port, speed, sid): break;
                        except (
                                ValueError,
                                minimalmodbus.NoResponseError,
                                minimalmodbus.InvalidResponseError
                        ) as e:
                            print(e)

            except serial.serialutil.SerialException as e:
                print(e)
               #self.devices[0].serial.close()

        if len(self.devices) > 0:
            print("Found ", len(self.devices), " devices. ")
            return True
        raise self.ServerError(
            "Current ports: \n" + "\n".join(ports) + "\nDevice Not found"

        )

    def main(self, inpt):
        args = inpt.split()
        if args[0] in self.consol:
            return self.consol[args[0]](args)
        return None


if __name__ == '__main__':
    srv = Server()
    srv.main(inpt="connect COM8 9600 1")
    srv.main(inpt="devices")
    srv.devices[0].device.read_registers(
        8,
       2,
        functioncode=3)
   #  srv.main(inpt="read 0 * 3")
   # # srv.main(inpt="read 1 * 4")
   #  print(srv.devices[0].holdings)
   #  srv.main(inpt="write 0 3 5")
   #  #srv.main(inpt="read 0 0 3")
   #  print(srv.devices[0].holdings)


