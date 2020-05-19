import datetime
import json
import multiprocessing
import os
import minimalmodbus
import serial
import serial as serialutil
import time


class Schn_Device(object):

    def __init__(self, resultQ, instrument):
        self.instrument: minimalmodbus.Instrument = instrument
        self.resultQ = resultQ
        self.slave_name = ""
        self.connection_error_count = 0
        self.dev_status = ""
        self.adr = 2
        self.indicators = []

    def write_console(self, mes):
        tmp_str = 'SCHN message: %s' % mes
        self.resultQ.put(tmp_str)

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

    def get_indicators(self):
        self.instrument.address = self.adr
        try:
            self.indicators = self.instrument.read_registers(3201, 11, functioncode=3)
            tmp = self.createRegReq(["SCHN_h"] * len(self.indicators), self.indicators, range(3201, 3212))
            self.resultQ.put(tmp)
            # print(tmp)
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(e)
            self.write_console(str(e))

    def refresh(self):
        self. instrument.address = self.adr
        print("Refreshing ATV71 device")
        self.slave_name = "нет устройства"
        self.connection_error_count = 0
        self.dev_status = None
        self.write_console("Connection reset")

        try:
            req = self.instrument._perform_command(43, '\x0E\x01\x00')
            self.slave_name = req[23:37]
            print("Schneider ID: "+self.slave_name)
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(e)
            self.write_console(str(e))

        self.get_indicators()

        tmp_id = self.slave_name
        tmp_str = '{"SCHN_ID" : {"value" : "%s"} }' % tmp_id
        self.resultQ.put(tmp_str)
        self.write_console(tmp_str)

    def start(self):
        self.instrument.address = self.adr
        print("ATV71 starting")

        self.instrument.write_register(8501, 0x1 + 0x8 + 0x800)

    def stop(self):
        self.instrument.address = self.adr
        self.instrument.write_register(8501, 0)

    def reset(self):
        self.instrument.address = self.adr
        print("ATV71 fault reset")
        self.instrument.write_register(8501, 0x00)
        self.instrument.write_register(8501, 0x80)

    def set_freq(self, freq):
        self.instrument.address = self.adr
        self.instrument.write_register(8502, freq)

    def get_freq(self):
        self.instrument.address = self.adr
        return 0

    def set_gtorque(self, val):
        self.instrument.address = self.adr
        self.instrument.write_register(9212, val)


    def get_gtorque(self):
        self.instrument.address = self.adr
        tmp = self.instrument.read_registers(9212, 1, functioncode=3)
        return tmp

    def set_mtorque(self, val):
        self.instrument.address = self.adr
        self.instrument.write_register(9211, val)

    def get_mtorque(self):
        self.instrument.address = self.adr
        tmp = self.instrument.read_registers(9211, 1, functioncode=3)
        return tmp

    def get_state(self):
        atv_state = [
            'Ready to ON', 'Swithed ON', 'Oper enbl1', 'Fault',
            'Vltg dsbl', 'Quick stop', 'Switch on dsbl', 'Alarm',
            'nf1', 'NoFrcdMode', 'StadyState', 'LFRDRefExc', 'nf', 'nf',
            'StopKeyEnbl', 'Revers'
        ]
        self.instrument.address = self.adr
        tmp = self.instrument.read_registers(3201, 1, functioncode=3)
        bnr = format(int(tmp[0]), 'b')
        for bit, st in zip(bnr, atv_state):
            print(st,":",bit)
        return 0


if __name__ == '__main__':

    port = "/dev/ttyUSB0"
    instrument = minimalmodbus.Instrument(port, 2)
    instrument.serial.baudrate = 9600
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 0.50  # seconds
    instrument.debug = False
    instrument.close_port_after_each_call = False

    resultQ = multiprocessing.Queue()
    schndr = Schn_Device(resultQ, instrument)
    schndr.refresh()
    schndr.get_indicators()
    schndr.reset()
    schndr.set_freq(10)
    # schndr.start()
    schndr.stop()
    schndr.set_gtorque(0)
    print("gen ", schndr.get_gtorque())
    # schndr.stop()
    schndr.get_state()
    while True:
        schndr.get_indicators()
        time.sleep(0.5)
