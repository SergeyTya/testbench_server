import datetime
import json
import os

import math
import multiprocessing
import sys
import termios
from io import StringIO

import minimalmodbus
import time
import server

now = datetime.datetime.now()

class RedirectedStdout:
    def __init__(self):
        self._stdout = None
        self._string_io = None

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._string_io = StringIO()
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self._stdout

    def __str__(self):
        return self._string_io.getvalue()


class Commands(object):
    MPCH_Get_AllHoldings = "MPCH_Get_AllHoldings"
    MPCH_Get_OneHolding = "MPCH_Get_OneHolding"
    MPCH_Get_SlaveID = "MPCH_Get_SlaveID"
    MPCH_Get_Status = "MPCH_Get_Status"
    MPCH_Set_OneHolding = "MPCH_Set_OneHolding"
    MPCH_saveToFile = "MPCH_saveToFile"
    MPCH_reconnect = "MPCH_reconnect"

class MPCH_Server(server.Server):

    def __init__(self, resultQ):

        self.resultQ = resultQ
        self.logfile = ""
        super().__init__()
        tmp = sys.stdout
        self.write_console(tmp)
        self.sincnt = 0

        try:
            with open('status.json', 'r',
                  encoding='Windows-1251'
                     ) as fh:
                self.satus_list = json.load(fh)
        except (
            json.decoder.JSONDecodeError,
            FileNotFoundError,
            UnicodeDecodeError
        ) as e: print(e)

    def createRegReq(self, name, ireg, adr, color=""):
        if color == "":
            tmp_str = "{" + ','.join(list(map(
                lambda nm, x, y: '"%s%d":{"value":"%d"} ' % (nm, y, x), name, ireg, adr
            ))) + "}"
        else:
            tmp_str = "{" + ','.join(list(map(
                lambda nm, x, y, z: '"%s%d":{"value":"%d" , "color" : "%s"} ' % (nm, y, x, z), name, ireg, adr, color
            ))) + "}"
        return tmp_str

    def getAllHoldings(self, **kwargs):
        self.main(inpt="read 0 * 3")
        self.resultQ.put(self.createRegReq(
            ["MPCH_hreg"] * len(self.devices[0].holdings),
            self.devices[0].holdings,
            range(len(self.devices[0].holdings)),
            ["white"] * len(self.devices[0].holdings),
        ))

    def setOneHolding(self, adr, value, **kwargs):
        try:
            value = int(value)
            adr = int(adr)
        except ValueError: return
        self.main(inpt="write 0 %d %d" % (adr, value))
        self.getOneHolding(adr)

    def getOneHolding(self, adr, **kwargs):
        try:
            num = int(adr)
        except ValueError: return
        self.main(inpt="read 0 %s 3" % adr)
        self.resultQ.put(self.createRegReq(
            ["MPCH_hreg"],
            [self.devices[0].holdings[num]],
            [num],
            ["white"]
        ))

    def getAllInputs(self, **kwargs):
        self.main(inpt="read 0 * 4")
        self.sincnt = self.sincnt + 0.1
        self.devices[0].inputs[3] = math.sin(self.sincnt)*1000
        self.devices[0].inputs[4] = 3670

        if len(self.devices[0].inputs) > 3:
            tmp = self.createRegReq(["MPCH_ireg"]*len(self.devices[0].inputs),self.devices[0].inputs[3:], range(6))
            self.resultQ.put(tmp)
            # json_data = json.dumps(tmp)
            self.logfile.write(tmp+'\n')
            self.logfile.flush()
            if os.path.getsize(self.logfile.name) > (1024 * 1024 * 2):
                self.create_logfile()

    def getId(self, **kwargs):
        tmp_id = "нет устройства"
        if len(self.devices) != 0:
            tmp_id= self.devices[0].slave_name
        tmp_str = '{"MPCH_ID" : {"value" : "%s"} }' % tmp_id
        self.resultQ.put(tmp_str)
        self.write_console(tmp_str)

    def getStatus(self, **kwargs):
        tmp_str = ""
        if len(self.devices) > 0:
            if len(self.devices[0].inputs) > 2:
                str_status = str(hex(self.devices[0].inputs[2]))
                try:
                    str_status2 = " " + self.satus_list[0][str_status[2:3]][0]+" "+self.satus_list[1][str_status[3:5]]
                    tmp_str = '{"MPCH_Status" : {"value" : "%s" , "color":"%s"} }' \
                              % (str_status2, self.satus_list[0][str_status[2:3]][1])

                except (
                        KeyError,
                        IndexError
                ): str_status2 = str_status
        else:
            tmp_str = '{"MPCH_ID" : {"value" : "%s"} }' % " нет устройства "
            self.resultQ.put(tmp_str)
            tmp_str = '{"MPCH_Status" : {"value" : "%s" , "color":"%s"} }' \
                      % ("нет устройства", "gray")
        self.resultQ.put(tmp_str)

    def saveToFile(self, **kwargs):
        #TODO save current holding to file
        tmp_str = '{"MPCH_saveToFile" : {"value" : "DONE"} }'
        self.resultQ.put(tmp_str)

    def write_console(self, mes):
        tmp_str = 'MPCH message: %s' % mes
        self.resultQ.put(tmp_str)

    def create_logfile(self):
        name = now.strftime("%d%m%Y%H%M") + "_" + self.devices[0].slave_name
        try:
            if self.logfile != "": self.logfile.close()
        except FileNotFoundError:
            pass
        self.logfile = open('static/logs/' + name + '.json', 'w')

    def reconnect(self, adr=1, **kwargs):
        print("Connection reset")
        self.write_console("Connection reset")
        try:
            adr = int(adr)
        except ValueError:
            print('ValueError')
            self.write_console("ValueError")
            adr = 1
        if adr == 0: adr = 1
        self.devices = []
        print("New connection Adr=%d" % adr)
        self.write_console("New connection Adr=%d" % adr)
        try:
            with RedirectedStdout() as out:
                self.main(inpt="connect * * %d" % adr)
                tmp = str(out)
                self.write_console(tmp)
            print(tmp)
            self.create_logfile()
        except server.Server.ServerError as e:
            tmp = str(out)
            self.write_console(tmp)
            print(tmp)
            print(e)
            self.write_console("error "+str(e))

class TestBench(multiprocessing.Process):

    cnt = 0

    def __init__(self, taskQ, resultQ):
        multiprocessing.Process.__init__(self)
        self.taskQ = taskQ
        self.resultQ = resultQ
        self.MPCH = MPCH_Server(resultQ)
        self.connection_error_count = 0

        try:
            # self.MPCH.main(inpt="connect COM8 9600 1")
            # self.MPCH.main(inpt="devices")
            self.MPCH.reconnect()


        except server.Server.ServerError as e:
            print(e)
            self.MPCH.write_console(e)

        self.command = {
            Commands.MPCH_Get_AllHoldings: self.MPCH.getAllHoldings,
            Commands.MPCH_Get_SlaveID: self.MPCH.getId,
            Commands.MPCH_Get_Status: self.MPCH.getStatus,
            Commands.MPCH_Get_OneHolding: self.MPCH.getOneHolding,
            Commands.MPCH_Set_OneHolding: self.MPCH.setOneHolding,
            Commands.MPCH_saveToFile: self.MPCH.saveToFile,
            Commands.MPCH_reconnect: self.MPCH.reconnect
        }

    def write_console(self, mes):
        tmp_str = 'Serial thread: %s' % mes
        self.resultQ.put(tmp_str)

    def close(self):
        pass

    def run(self):
        while True:
            try:
                self.proc()
            except termios.error as e:
                print(e)
                self.write_console("Port IO error")
                self.MPCH.devices = []
            # except:
            #     print(" Thread unexpected error!! ")
            #     self.write_console("Unexpected error")
            #     self.MPCH.devices = []

    def proc(self):
        time.sleep(0.5)

        self.MPCH.getStatus()
        if len(self.MPCH.devices) == 0:
            self.MPCH.write_console("Device not found")
            while not self.taskQ.empty():
                tmp = self.taskQ.get()
                try:
                    dict = json.loads(tmp)
                except json.decoder.JSONDecodeError as e:
                    self.MPCH.write_console("Command decode error")
                    print(e)
                    return
                if dict["CMD"] == Commands.MPCH_reconnect:
                    self.MPCH.reconnect(value=dict["VL"], adr=dict["ADR"])
            time.sleep(1)

            return

        self.MPCH.getAllInputs()
        self.cnt = self.cnt + 1
        time.sleep(0.1)
        self.cnt = self.cnt + 1
        time.sleep(0.1)
        tmp_str = '{"MPCH_ConCnt" : {"value" : "%d"} }' % self.cnt
        self.resultQ.put(tmp_str)

        while not self.taskQ.empty():
            self.cnt = self.cnt + 1
            tmp = self.taskQ.get()
            print("get task: ", tmp)
            try:
                dict = json.loads(tmp)
            except json.decoder.JSONDecodeError as e:
                self.MPCH.write_console("Command decode error")
                print(e)
                return
            try:
                value = dict["VL"]
            except KeyError:
                value = 0
            try:
                adr = dict["ADR"]
            except KeyError:
                adr = 0
            try:
                self.command[dict["CMD"]](value=value, adr=adr)
                self.write_console("done")
            except KeyError as e:
                print('KeyError'+str(e))
                self.write_console('KeyError'+str(e))
            except (
                    minimalmodbus.NoResponseError,
                    minimalmodbus.InvalidResponseError,
            ) as e:
                print(e)
                self.connection_error_count = self.connection_error_count + 1
                tmp_str = '{"MPCH_ConErr" : {"value" : "%d"} }' % self.connection_error_count
                self.resultQ.put(tmp_str)





