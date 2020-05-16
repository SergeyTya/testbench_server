import datetime
import json
import multiprocessing
import os
import minimalmodbus
import serial


class Schn_Device(object):

    def __init__(self, resultQ, serial_port: serial.Serial):
        self.instrument: minimalmodbus.Instrument = minimalmodbus.Instrument(serial_port.port, 2)
        self.instrument.serial = serial_port
        self.instrument.debug = False
        self.instrument.close_port_after_each_call = False
        self.resultQ = resultQ
        self.slave_name = ""
        self.connection_error_count = 0
        self.dev_status = ""

    def write_console(self, mes):
        tmp_str = 'SCHN message: %s' % mes
        self.resultQ.put(tmp_str)

    def refresh(self):
        print("Refreshing ATV71 device")
        self.slave_name = "нет устройства"
        self.connection_error_count = 0
        self.dev_status = None
        self.write_console("Connection reset")

        try:
            req = self.instrument._perform_command(43, '\x0E\x01\x00')

        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(e)
            self.write_console(str(e))
            self.holdings = []
            self.inputs = []

        tmp_id = self.slave_name
        tmp_str = '{"SCHN_ID" : {"value" : "%s"} }' % tmp_id
        self.resultQ.put(tmp_str)
        self.write_console(tmp_str)
