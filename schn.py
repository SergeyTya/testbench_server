import ctypes
import datetime
import json
import multiprocessing
import os
import minimalmodbus
import serial
import serial as serialutil
import time

schn_iname = ['Speed, rmp', 'Current, A', 'Torque, %', 'Volt, V', '5', '6', '7', '8', '9']

class Schn_Device(object):

    def __init__(self, resultQ, instrument):
        self.instrument: minimalmodbus.Instrument = instrument
        self.resultQ = resultQ
        self.slave_name = ""
        self.connection_error_count = 0
        self.dev_status = 0xffff
        self.adr = 2
        self.indicators = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.connected: bool = False
        self.enabled = False


    def write_console(self, mes):
        tmp_str = 'SCHN message: %s' % mes
        self.resultQ.put(tmp_str)

    def createRegReq(self, name, ireg, adr, color=""):
        if color == "":
            tmp_str = "{" + ','.join(list(map(
                lambda nm, x, y: '"%s%d":{"value":"%5.1f"} ' % (nm, y, x), name, ireg, adr
                # lambda nm, x, y: '"%s%d":{"value":"%d"} ' % (nm, y, x), name, ireg, adr
            ))) + "}"
        else:
            tmp_str = "{" + ','.join(list(map(
                 lambda nm, x, y, z: '"%s%d":{"value":"%5.1f" , "color" : "%s"} ' % (nm, y, x, z), name, ireg, adr, color
                # lambda nm, x, y, z: '"%s%d":{"value":"%d" , "color" : "%s"} ' % (nm, y, x, z), name, ireg, adr, color
            ))) + "}"
        return tmp_str

    def get_indicators(self):
        self.instrument.address = self.adr
        self.get_status()
        if not self.enabled: return
        if not self.connected:
            self.get_slaveID()
            if not self.connected: return
        try:
            # current + torque
            tmp = self.instrument.read_registers(3201, 5, functioncode=3)
            self.dev_status = tmp[0]
            self.indicators[1] = ctypes.c_int16(tmp[3]).value * 0.1    # curr
            self.indicators[2] = ctypes.c_int16(tmp[4]).value * 0.1    # Torque
            # speed
            tmp = self.instrument.read_registers(8604, 1, functioncode=3)[0]
            self.indicators[0] = ctypes.c_int16(tmp).value
            # frequency reference
            self.indicators[3] = ctypes.c_int16(self.instrument.read_registers(8502, 1, functioncode=3)[0]).value * 0.1
            # Torque limits
            tmp = self.instrument.read_registers(9211, 2, functioncode=3)
            self.indicators[4] = tmp[1]*0.1  # generator mode
            self.indicators[5] = tmp[0]*0.1  # motor mode

            tmp = self.createRegReq(["SchnI"] * len(self.indicators), self.indicators, range(6))
            self.resultQ.put(tmp)
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : Schn :", e)
            self.write_console(str(e))
            self.set_disconnected()

    def refresh(self, **kwargs):
        if not self.enabled: return
        self. instrument.address = self.adr
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "Refreshing ATV71 device")
        self.slave_name = "нет устройства"
        self.connection_error_count = 0
        self.dev_status = 0xffff
        self.write_console("Connection reset")

        try:
            req = self.instrument._perform_command(43, '\x0E\x01\x00')
            self.slave_name = req[23:37]
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "Schneider ID: "+self.slave_name)
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            self.connection_error_count = self.connection_error_count + 1
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : Schn :", e)
            self.write_console(str(e))
            self.set_disconnected()
        self.get_indicators()
        tmp_id = self.slave_name
        tmp_str = '{"Schn_ID" : {"value" : "%s"} }' % tmp_id
        self.resultQ.put(tmp_str)
        self.write_console(tmp_str)

    def set_disconnected(self, **kwargs):
        self.slave_name = "disconnected"
        self.connected: bool = False
        tmp_str = '{"Schn_ID" : {"value" : "%s"} }' % self.slave_name
        self.resultQ.put(tmp_str)
        self.write_console(tmp_str)

    def set_enable(self, **kwargs):
        self.enabled = True
        tmp_str = '{"Schn_enable_state" : {"value" : "Включен", "color": "green"}}'
        self.resultQ.put(tmp_str)

    def set_disable(self, **kwargs):
        self.enabled = False
        tmp_str = '{"Schn_enable_state" : {"value" : "Отключен", "color": "red"}}'
        self.resultQ.put(tmp_str)

    def start(self, **kwargs):
        if not self.enabled: return
        self.instrument.address = self.adr
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "ATV71 start")
        self.instrument.write_register(8601, 0x1 + 0x8)

    def stop(self, **kwargs):
        if not self.enabled: return
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "ATV71 stop")
        self.instrument.address = self.adr
        self.instrument.write_register(8501, 0)

    def reset(self, **kwargs):
        if not self.enabled: return
        self.instrument.address = self.adr
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "ATV71 fault reset")
        self.instrument.write_register(8501, 0x00)
        self.instrument.write_register(8501, 0x80)

    def revers(self, **kwargs):
        if not self.enabled: return
        self.instrument.address = self.adr
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "ATV71 revers")
        self.instrument.write_register(8501, 2048)

    def set_freq(self, value,  **kwargs):
        if not self.enabled: return
        try:
            value = int(value)
        except ValueError:
            return
        self.instrument.address = self.adr
        self.instrument.write_register(8502, value, signed=True)

    def set_gtorque(self, value,  **kwargs):
        if not self.enabled: return
        try:
            value = int(value)
        except ValueError:
            return
        self.instrument.address = self.adr
        self.instrument.write_register(9212, value)
        # tmp_str = '{"SchnI4" : {"value" : "%s"} }' % value
        # self.resultQ.put(tmp_str)


    def set_mtorque(self, value,  **kwargs):
        if not self.enabled: return
        try:
            value = int(value)
        except ValueError:
            return
        self.instrument.address = self.adr
        self.instrument.write_register(9211, value)

    def get_status(self,  **kwargs):

        if not self.enabled:
            tmp_str = '{"Schn_St" : {"value" : "нет связи", "color": "gray"}}'
            self.resultQ.put(tmp_str)
            tmp_str = '{"Schn_enable_state" : {"value" : "Отключен", "color": "red"}}'
            self.resultQ.put(tmp_str)
            return False

        atv_state = [
            'Ready to ON', 'Swithed ON', 'Oper enbl1', 'Fault',
            'Vltg dsbl', 'Quick stop', 'Switch on dsbl', 'Alarm',
            'nf1', 'NoFrcdMode', 'StadyState', 'LFRDRefExc', 'nf', 'nf',
            'StopKeyEnbl', 'Revers'
        ]
        self.instrument.address = self.adr
        bnr = format( int(self.dev_status), 'b').zfill(16)
        tmp_str = '{"Schn_St" : {"value" : " "},  {"color" : "blue" } }'
        strng = str(self.dev_status)+" "

        # for i in range(16):
        #     if bnr[i] == "1": strng = strng + atv_state[15-i] + " " + str(i) + "; "
        # tmp_str = '{"Schn_St" : {"value" : "%s"} }' % strng

        if bnr[14] == '1': tmp_str = '{"Schn_St" : {"value" : "Остановлен" , "color": "blue"} }'
        if bnr[13] == '1': tmp_str = '{"Schn_St" : {"value" : "Работа" , "color": "green"} }'
        if bnr[12] == '1': tmp_str = '{"Schn_St" : {"value" : "Авария", "color": "red"} }'
        if not self.connected: tmp_str = '{"Schn_St" : {"value" : "нет связи", "color": "gray"}}'

        # print(tmp_str)

        self.resultQ.put(tmp_str)
        # self.write_console(tmp_str)
        return strng

    def get_slaveID(self, **kwargs):
        if not self.enabled: return
        self.instrument.address = self.adr
        self.slave_name = "disconnected"
        try:
            req = self.instrument._perform_command(43, '\x0E\x01\x00')
            self.slave_name = req[23:37]
            self.write_console("Schn_ID: " + self.slave_name)
            tmp_str = '{"Schn_ID" : {"value" : "%s"} }' % self.slave_name
            self.resultQ.put(tmp_str)
            self.write_console(tmp_str)
            self.connected = True
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "Schn ID: ", self.slave_name)
            self.get_status()
            return True
        except (
                minimalmodbus.InvalidResponseError,
                minimalmodbus.ModbusException,
                minimalmodbus.NoResponseError) as e:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : Schn :", e)
            self.write_console(str(e))
            return False

if __name__ == '__main__':
    #
    # port = "/dev/ttyUSB0"
    # instrument = minimalmodbus.Instrument(port, 2)
    # instrument.serial.baudrate = 9600
    # instrument.serial.bytesize = 8
    # instrument.serial.parity = serial.PARITY_NONE
    # instrument.serial.stopbits = 1
    # instrument.serial.timeout = 0.50  # seconds
    # instrument.debug = False
    # instrument.close_port_after_each_call = False
    #
    # resultQ = multiprocessing.Queue()
    # schndr = Schn_Device(resultQ, instrument)
    # schndr.refresh()
    # schndr.get_indicators()
    # schndr.reset()
    # schndr.set_freq(10)
    # # schndr.start()
    # schndr.stop()
    # schndr.set_gtorque(0)
    # print("gen ", schndr.get_gtorque())
    # # schndr.stop()
    # schndr.get_status()
    # while True:
    #     schndr.get_indicators()
    #     time.sleep(0.5)

    a =65000
    print(ctypes.c_int16(a).value)