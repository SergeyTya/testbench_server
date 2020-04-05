import json
import multiprocessing
import time
import server


class Commands(object):
    MPCH_Get_AllHoldings = "MPCH_Get_AllHoldings"
    MPCH_Get_OneHolding = "MPCH_Get_OneHolding"
    MPCH_Get_SlaveID = "MPCH_Get_SlaveID"
    MPCH_Get_Status = "MPCH_Get_Status"
    MPCH_Set_OneHolding = "MPCH_Set_OneHolding"
    MPCH_saveToFile = "MPCH_saveToFile"

class MPCH_Server(server.Server):

    def __init__(self, resultQ):
        super().__init__()
        self.resultQ = resultQ
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
        # формирование json строки из массива регистров заданного типа
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
        if len(self.devices[0].inputs) > 3:
            self.resultQ.put(self.createRegReq(
                ["MPCH_ireg"]*len(self.devices[0].inputs),
                self.devices[0].inputs[3:],
                range(len(self.devices[0].inputs))
            ))

    def getId(self, **kwargs):
        tmp_str = '{"MPCH_ID" : {"value" : "%s"} }' % self.devices[0].slave_name
        self.resultQ.put(tmp_str)

    def getStatus(self, **kwargs):

        if len(self.devices) > 0:
            if len(self.devices[0].inputs) > 2:
                str_status = str(hex(self.devices[0].inputs[2]))
                try:
                    str_status2 = " " + self.satus_list[0][str_status[2:3]][0]+" "+self.satus_list[1][str_status[3:5]]
                    tmp_str = '{"MPCH_Status" : {"value" : "%s" , "color":"%s"} }' \
                              % (str_status2, self.satus_list[0][str_status[2:3]][1])
                    self.resultQ.put(tmp_str)
                except (
                        KeyError,
                        IndexError
                ): str_status2 = str_status

    def saveToFile(self, **kwargs):
        #TODO save current holding to file
        tmp_str = '{"MPCH_saveToFile" : {"value" : "DONE"} }'
        self.resultQ.put(tmp_str)




                # if self.send_errcnt > 10: str_status2 = " нет связи "
                # self.label_DevStatus.setText(str_status2)




class TestBench(multiprocessing.Process):

    cnt = 0

    def __init__(self, taskQ, resultQ):
        multiprocessing.Process.__init__(self)
        self.taskQ = taskQ
        self.resultQ = resultQ

        self.MPCH = MPCH_Server(resultQ)
        self.MPCH.main(inpt="connect COM8 9600 1")
        self.MPCH.main(inpt="devices")

        self.command = {
            Commands.MPCH_Get_AllHoldings: self.MPCH.getAllHoldings,
            Commands.MPCH_Get_SlaveID: self.MPCH.getId,
            Commands.MPCH_Get_Status: self.MPCH.getStatus,
            Commands.MPCH_Get_OneHolding: self.MPCH.getOneHolding,
            Commands.MPCH_Set_OneHolding: self.MPCH.setOneHolding,
            Commands.MPCH_saveToFile: self.MPCH.saveToFile
        }

    def close(self):
        pass

    def run(self):
        while True:
            self.proc()


    def proc(self):
        time.sleep(0.1)
        if len(self.MPCH.devices) > 0:
            self.MPCH.getAllInputs()
            self.cnt = self.cnt + 1
            time.sleep(0.1)
            self.MPCH.getStatus()
            self.cnt = self.cnt + 1
            time.sleep(0.1)
            tmp_str = '{"MPCH_ConCnt" : {"value" : "%d"} }' % self.cnt
            self.resultQ.put(tmp_str)

            while not self.taskQ.empty():
                self.cnt = self.cnt + 1
                tmp = self.taskQ.get()
                print("get task: ", tmp)
                dict = json.loads(tmp)
                try: value = dict["VL"]
                except KeyError: value = 0
                try: adr = dict["ADR"]
                except KeyError: adr = 0
                self.command[dict["CMD"]](value=value, adr=adr)
