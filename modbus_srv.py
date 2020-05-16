import json
import multiprocessing
import termios
import minimalmodbus
import serial
import time
import serial as serialutil
import mpch
import schn


class Commands(object):
    MPCH_Get_AllHoldings = "MPCH_Get_AllHoldings"
    MPCH_Get_OneHolding = "MPCH_Get_OneHolding"
    MPCH_Get_SlaveID = "MPCH_Get_SlaveID"
    MPCH_Get_Status = "MPCH_Get_Status"
    MPCH_Set_OneHolding = "MPCH_Set_OneHolding"
    MPCH_saveToFile = "MPCH_saveToFile"
    MPCH_reconnect = "MPCH_reconnect"


class TestBench(multiprocessing.Process):

    def __init__(self, taskQ, resultQ):
        multiprocessing.Process.__init__(self)
        self.taskQ = taskQ
        self.resultQ = resultQ

        port = "/dev/ttyACM1"
        serial_port = serialutil.Serial(port)
        serial_port.baudrate = 9600
        serial_port.bytesize = 8
        serial_port.parity = serial.PARITY_NONE
        serial_port.stopbits = 1
        serial_port.timeout = 0.50  # seconds
        self.MPCH = mpch.MPCH_Device(resultQ, serial_port)
        self.Schn = schn.Schn_Device(resultQ, serial_port)
        self.MPCH.refresh()
        self.Schn.refresh()

        self.connection_error_count = 0

        self.command = {
            Commands.MPCH_Get_AllHoldings: self.MPCH.getAllHoldings,
            Commands.MPCH_Get_SlaveID: self.MPCH.refresh,
            Commands.MPCH_Get_Status: self.MPCH.getStatus,
            Commands.MPCH_Get_OneHolding: self.MPCH.getOneHolding,
            Commands.MPCH_Set_OneHolding: self.MPCH.setOneHolding,
            Commands.MPCH_saveToFile: self.MPCH.saveToFile,
            Commands.MPCH_reconnect: self.MPCH.refresh
        }

    def write_console(self, mes):
        tmp_str = 'Serial thread: %s' % mes
        self.resultQ.put(tmp_str)

    def close(self):
        pass

    def read_tasks(self):
        while not self.taskQ.empty():
            self.cnt = self.cnt + 1
            tmp = self.taskQ.get()
            print("get task: ", tmp)
            self.MPCH.writeCmdLog(tmp)
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
                # self.write_console("done")
            except KeyError as e:
                print('KeyError' + str(e))
                self.write_console('KeyError' + str(e))
            except (
                    minimalmodbus.NoResponseError,
                    minimalmodbus.InvalidResponseError,
            ) as e:
                print(e)
                self.MPCH.connection_error_count = self.MPCH.connection_error_count + 1

    def run(self):
        while True:
            try:
                self.proc()
            except termios.error as e:
                print(e)
                self.write_console("Port IO error")
            # except:
            #     print(" Thread unexpected error!! ")
            #     self.write_console("Unexpected error")
            #     self.MPCH.devices = []

    def proc(self):
        tmp_str = '{"MPCH_ConCnt" : {"value" : "%d"} }' % self.cnt
        self.resultQ.put(tmp_str)
        self.cnt = self.cnt + 1
        time.sleep(0.5)
        self.MPCH.getAllInputs()
        self.MPCH.getStatus()

        if self.connection_error_count != self.MPCH.connection_error_count:
            self.connection_error_count = self.MPCH.connection_error_count
            tmp_str = '{"MPCH_ConErr" : {"value" : "%d"} }' % self.connection_error_count
            self.resultQ.put(tmp_str)

        self.read_tasks()




