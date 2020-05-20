import datetime
import json
import multiprocessing
import os
import minimalmodbus
import serial


class MPCH_Device(object):

    def __init__(self, resultQ , instrument):
        self.instrument: minimalmodbus.Instrument = instrument
        self.resultQ = resultQ
        self.logfileIndic = ""
        self.logfileCmd = ""
        self.connection_error_count = 0
        self.dev_status = ""
        self.holdings = []
        self.inputs = []
        self.slave_name = ""
        self.create_logfile()
        self.adr = 1
        self.connected:bool = False

        try:
            with open('status.json', 'r',
                  encoding='Windows-1251'
                     ) as fh:
                self.satus_list = json.load(fh)
        except (
            json.decoder.JSONDecodeError,
            FileNotFoundError,
            UnicodeDecodeError
        ) as e: print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ",e)

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
        self.instrument.address = self.adr
        if not self.connected:
            self.get_slaveID()
            if not self.connected: return
        if len(self.inputs) < 3: return
        try:
            self.holdings = self.instrument.read_registers(0, self.inputs[1], functioncode=3)
            tmp = self.createRegReq(["MPCH_hreg"] * len(self.holdings), self.holdings,
                                    range(len(self.holdings)),["white"] * len(self.holdings),)
            self.resultQ.put(tmp)
            self.writeCmdLog(tmp)
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : MPCH :", e)
            self.set_disconnected()

    def setOneHolding(self, adr, value, **kwargs):
        self.instrument.address = self.adr
        try:
            value = int(value)
            adr = int(adr)
        except ValueError: return
        if not self.connected:
            self.get_slaveID()
            if not self.connected: return
        if len(self.holdings) < adr: return
        try:
            self.instrument.write_register(adr, value, signed=False)
            # print("Set holding %d: %d" % (adr, value))

            self.getOneHolding(adr)
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : MPCH :", e)
            self.set_disconnected()


    def getOneHolding(self, adr, **kwargs):
        self.instrument.address = self.adr
        if not self.connected: self.get_slaveID()
        try:
            num = int(adr)
        except ValueError: return
        if len(self.holdings) < adr: return
        if not self.connected:
            self.get_slaveID()
            if not self.connected: return
        try:
            tmp = self.instrument.read_register(adr, 0, functioncode=3)
            # print("Get holding %d: %d" % (adr, tmp))
            if adr < len(self.holdings): self.holdings[adr] = tmp
            tmp = self.createRegReq(
                ["MPCH_hreg"],
                [self.holdings[num]],
                [num],
                ["white"])
            self.resultQ.put(tmp)
            self.writeCmdLog(tmp)
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : MPCH :", e)
            self.set_disconnected()

    def set_disconnected(self):
        self.slave_name = "disconnected"
        self.connected: bool = False
        tmp_str = '{"MPCH_ID" : {"value" : "%s"} }' % self.slave_name
        self.resultQ.put(tmp_str)
        self.write_console(tmp_str)
        self.writeCmdLog(tmp_str)

    def getAllInputs(self, **kwargs):
        self.instrument.address = self.adr
        if not self.connected:
            self.get_slaveID()
            if not self.connected: return
        try:
            if not self.connected: self.get_slaveID()
            if len(self.inputs) < 3: return
            self.inputs = self.instrument.read_registers(0, self.inputs[0], functioncode=4)
            tmp = self.createRegReq(["MPCH_ireg"] * len(self.inputs), self.inputs[3:], range(6))
            self.resultQ.put(tmp)
            now = datetime.datetime.now().strftime('"%Y-%m-%d %H:%M:%S", ')
            tmp = tmp[:1] + '"time":' + now + tmp[1:]
            self.logfileIndic.write(tmp + '\n')
            # self.logfile.flush()
            if os.path.getsize(self.logfileIndic.name) > (1024 * 1024 * 2):
                self.create_logfile()

        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : MPCH :", e)
            self.set_disconnected()


    def refresh(self, **kwargs):
        self.instrument.address = self.adr
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "Refreshing MPCH device")
        self.slave_name = "нет устройства"
        self.connection_error_count = 0
        self.dev_status = None
        self.write_console("Connection reset")

        try:
            req = self.instrument._perform_command(43, '\x0E\x01\x01\x00\x00')
            self.slave_name = req[8:16] + req[32:40] + req[44:52]
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "MPCH ID: ", self.slave_name)
            self.write_console("MPCH ID: " + self.slave_name)
            tmp = self.instrument.read_registers(0, 2, functioncode=4)
            print("Holdings count: ", tmp[1])
            print("Inputs count: ", tmp[0])
            self.write_console("Holdings count: " + str(tmp[1]))
            self.write_console("Inputs count: " +  str(tmp[0]))
            self.holdings = self.instrument.read_registers(0, tmp[1], functioncode=3)
            self.inputs = self.instrument.read_registers(0, tmp[0], functioncode=4)
            self.getStatus()
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : MPCH :", e)
            self.write_console(str(e))
            self.holdings = []
            self.inputs = []
            self.set_disconnected()
        tmp_id = self.slave_name
        tmp_str = '{"MPCH_ID" : {"value" : "%s"} }' % tmp_id
        self.resultQ.put(tmp_str)
        self.write_console(tmp_str)
        self.writeCmdLog(tmp_str)

    def get_slaveID(self, **kwargs):
        self.instrument.address = self.adr
        try:
            req = self.instrument._perform_command(43, '\x0E\x01\x01\x00\x00')
            self.slave_name = req[8:16] + req[32:40] + req[44:52]
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "MPCH ID: ", self.slave_name)
            self.write_console("MPCH ID: " + self.slave_name)
            tmp_str = '{"MPCH_ID" : {"value" : "%s"} }' % self.slave_name
            self.resultQ.put(tmp_str)
            self.write_console(tmp_str)
            self.writeCmdLog(tmp_str)
            self.connected = True
            return True
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : MPCH :", e)
            self.write_console(str(e))
            return False

    def getStatus(self, **kwargs):
        tmp_str = ""
        if len(self.inputs) > 2:
            str_status = str(hex(self.inputs[2]))
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
        if self.dev_status != tmp_str:
            self.dev_status = tmp_str
            self.writeCmdLog(tmp_str)

    def saveToFile(self, **kwargs):
        #TODO save current holding to file
        tmp_str = '{"MPCH_saveToFile" : {"value" : "DONE"} }'
        self.resultQ.put(tmp_str)

    def write_console(self, mes):
        tmp_str = 'MPCH message: %s' % mes
        self.resultQ.put(tmp_str)
        self.writeCmdLog(tmp_str)

    def create_logfile(self):
        now = datetime.datetime.now()
        name1 = now.strftime("%d%m%Y%H%M%S") + "_" + self.slave_name + "_indic.json"
        name2 = now.strftime("%d%m%Y%H%M%S") + "_" + self.slave_name + "_cmd.txt"
        try:
            if self.logfileIndic != "": self.logfileIndic.close()
            if self.logfileCmd != "": self.logfileCmd.close()
        except FileNotFoundError: pass
        self.logfileIndic = open('static/log/' + name1, 'x')
        self.logfileCmd = open('static/log/' + name2, 'x')

    def writeCmdLog(self, msg):
        if self.logfileCmd != "":
            self.logfileCmd.write(datetime.datetime.now().strftime("%d/%m/%Y-%H.%M.%S") + " : " + msg + '\n')
            self.logfileCmd.flush()


if __name__ == '__main__':

    port = "/dev/ttyUSB0"
    # port = "COM6"
    instrument = minimalmodbus.Instrument(port, 2)
    instrument.serial.baudrate = 9600
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 0.50  # seconds
    instrument.debug = False
    instrument.close_port_after_each_call = False
    resultQ = multiprocessing.Queue()

    MPCH = MPCH_Device(resultQ, instrument)
    MPCH.refresh()
    MPCH.getAllInputs()
    MPCH.getAllHoldings()
    MPCH.setOneHolding(2, 25)
    print(MPCH.holdings)
    print(MPCH.dev_status)
