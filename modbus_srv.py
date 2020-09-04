import datetime
import io
import json
import multiprocessing
# import termios
import termios
import ctypes
import minimalmodbus
import serial
import time
import serial as serialutil
import mpch
import schn
import os
import sys
import subprocess

libc = ctypes.CDLL(None)

class Commands(object):
    MPCH_Get_AllHoldings = "MPCH_Get_AllHoldings"
    MPCH_Get_OneHolding = "MPCH_Get_OneHolding"
    MPCH_Get_SlaveID = "MPCH_Get_SlaveID"
    MPCH_Get_Status = "MPCH_Get_Status"
    MPCH_Set_OneHolding = "MPCH_Set_OneHolding"
    MPCH_saveToFile = "MPCH_saveToFile"
    MPCH_reconnect = "MPCH_reconnect"
    Schn_getID = "Schn_getID"
    Schn_reconnect = "Schn_reconnect"
    Schn_setGenTorq = "Schn_setGenTorq"
    Schn_setMtrTorq = "Schn_setMtrTorq"
    Schn_setFreq = "Schn_setFreq"
    Schn_start = "Schn_start"
    Schn_stop =  "Schn_stop"
    Schn_reset = "Schn_reset"
    Loader_write = "loader_write"
    Loader_verify = "loader_verify"
    Loader_reset = "loader_reset"


class TestBench(multiprocessing.Process):

    def __init__(self, taskQ, resultQ):
        multiprocessing.Process.__init__(self)
        self.taskQ = taskQ
        self.resultQ = resultQ

        self.port = "/dev/ttyUSB1"
       # port = "COM7"
        instrument = minimalmodbus.Instrument(self.port, 2)
        instrument.serial.baudrate = 9600
        instrument.serial.bytesize = 8
        instrument.serial.parity = serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = 0.50  # seconds
        instrument.debug = False
        instrument.close_port_after_each_call = False

        self.MPCH = mpch.MPCH_Device(resultQ, instrument)
        self.Schn = schn.Schn_Device(resultQ, instrument)
        self.MPCH.refresh()
        self.Schn.refresh()

        self.connection_error_count = 0
        self.cnt = 0

        self.command = {
            Commands.MPCH_Get_AllHoldings: self.MPCH.getAllHoldings,
            Commands.MPCH_Get_SlaveID: self.MPCH.get_slaveID,
            Commands.MPCH_Get_Status: self.MPCH.getStatus,
            Commands.MPCH_Get_OneHolding: self.MPCH.getOneHolding,
            Commands.MPCH_Set_OneHolding: self.MPCH.setOneHolding,
            Commands.MPCH_saveToFile: self.MPCH.saveToFile,
            Commands.MPCH_reconnect: self.MPCH.refresh,
            Commands.Schn_getID: self.Schn.get_slaveID,
            Commands.Schn_reconnect: self.Schn.refresh,
            Commands.Schn_setGenTorq: self.Schn.set_gtorque,
            Commands.Schn_setFreq: self.Schn.set_freq,
            Commands.Schn_setMtrTorq: self.Schn.set_mtorque,
            Commands.Schn_reset: self.Schn.reset,
            Commands.Schn_start: self.Schn.start,
            Commands.Schn_stop: self.Schn.stop,
            Commands.Loader_write: self.loader_write,
            Commands.Loader_verify: self.loader_verify,
            Commands.Loader_reset: self.loader_reset
        }

    # run consol application with arguments
    def loader_proc(self, cmd):
        proc = subprocess.Popen('./loader/main %s 9600 1 %s ./temp_hex/temp.hex' % (self.port, cmd), shell=True,
                                stdout=subprocess.PIPE)
        s = ' '
        while s:
            s = proc.stdout.readline().decode('unicode_escape').rstrip()
            print(s)
            if s != '':
                tmp_str = '{"bconsol" : {"value" : "%s"} }' % s
                self.resultQ.put(tmp_str)

    # writing hex data from socket to temp file
    def loader_write_hex(self, data):
        path = os.getcwd() + '/temp_hex/'
        os.system('rm -rf %s/*' % path)
        os.system('touch %s/temp.hex' % path)
        data = data.replace(',', '\n')
        with open(path + 'temp.hex', 'w') as f:
            f.write(data)
            f.close

    def loader_reset(self, **kwargs):
        self.loader_proc("reset")

    def loader_write(self, value, **kwargs):
        self.loader_write_hex(value)
        self.loader_proc("flash")

    def loader_verify(self, value, **kwargs):
        self.loader_write_hex(value)
        self.loader_proc("verify")

    def write_console(self, mes):
        tmp_str = 'Serial thread: %s' % mes
        self.resultQ.put(tmp_str)

    def close(self):
        pass

    def read_tasks(self):
        while not self.taskQ.empty():
            self.cnt = self.cnt + 1
            tmp = self.taskQ.get()
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "get task: ", tmp)
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
                self.write_console('KeyError : ' + str(e))
            except (
                    minimalmodbus.NoResponseError,
                    minimalmodbus.InvalidResponseError,
            ) as e:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", e)
                self.MPCH.connection_error_count = self.MPCH.connection_error_count + 1

    def run(self):
        while True:
            try:
                self.proc()
            except termios.error as e:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", e)
                self.write_console("Port IO error")
            # except:
            #     print(" Thread unexpected error!! ")
            #     self.write_console("Unexpected error")
            #     self.MPCH.devices = []

    def proc(self):
        tmp_str = '{"MPCH_ConCnt" : {"value" : "%d"} }' % self.cnt
        self.resultQ.put(tmp_str)
        self.cnt = self.cnt + 1
        time.sleep(0.1)
        self.MPCH.getAllInputs()
        self.MPCH.getStatus()
        # self.Schn.get_indicators()

        if self.connection_error_count != self.MPCH.connection_error_count:
            self.connection_error_count = self.MPCH.connection_error_count
            tmp_str = '{"MPCH_ConErr" : {"value" : "%d"} }' % self.connection_error_count
            self.resultQ.put(tmp_str)

        self.read_tasks()

if __name__ == '__main__':
    proc = subprocess.Popen('./loader/main /dev/ttyUSB1 9600 1 verify ./temp_hex/temp.hex', shell=True,
                            stdout=subprocess.PIPE)
    s = ' '
    while s:
        s = proc.stdout.readline()
        # print(s)
        s=s.rstrip().decode('UTF8')
        print(s)