import json
import multiprocessing
from enum import Enum
from threading import Thread
from time import sleep
from modbus_srv import Commands as ModbusCommands


class Commands:
    Start = "sStart",
    Stop  = "sStop",
    Reset = "sReset",



class Scenario(object):

    Enabled: bool
    toServerList: multiprocessing.Queue()
    toDeviceList: multiprocessing.Queue()

    def _1sTimer(self):
        cnt = 0
        while(True):
            cnt = cnt + 1
            print("1 sec left")
            print(self.mpch._isOk)
            self._sendCommandToModbus(cmd=ModbusCommands.MPCH_Set_OneHolding, adr=1, value=cnt)
            sleep(1)


    class Device:

        class State:
            OK:str = "Готов"
            ISON:str = "Работа"

        _state: State
        _load: int
        _isOk: bool
        _isOn: bool
        _name: str

        def __init__(self, name: str):
            self._isOk = False
            self._isOn = False
            self._name = name

        @property
        def state(self):
            return self._state

        @state.setter
        def state(self, value: str):
            self._state = value
            self._isOk = self.State.OK in value or self._isOn
            self._isOn = self.State.ISON in value
            # self.print()

        def print(self):
            print(self._name)
            print(self._state)
            print(self._isOn)
            print(self._isOk)

    def __init__(self):
        self.mpch = self.Device("MPCH")
        self.schn = self.Device("SCHN")
        self.toDeviceList = multiprocessing.Queue()
        self.toServerList = multiprocessing.Queue()

        self.commands = {
            Commands.ScenarioEnable: self.enable
        }

        # self._1sTimer = Thread(target=self._1sTimer, daemon=True)
        # self._1sTimer.start()


    def readDeviceToServerMessage(self, mes:str):
        try:
            mes = json.loads(mes)

            try:
                self.mpch.state = mes['MPCH_Status']['value']
                return True
            except KeyError: pass

            try:
                self.schn.state = mes["Schn_St"]['value']
                return True
            except KeyError: pass

        except json.decoder.JSONDecodeError as e:
            return False
        return False

    def readServerToScenarioMessage(self):
        pass

    def _sendCommandToModbus(self, cmd, adr=0, value=0):
        temp: str = '{"CMD":"%s", "ADR":"%s", "VL":"%s"}' % (cmd, adr, value)
        self.toDeviceList.put(temp)

    def enable(self):
        pass
