import multiprocessing
import time
from threading import Timer

import modbus_srv
import tornado_srv
import scenario
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options
import datetime
import json
from threading import Thread

if __name__ == "__main__":

    mbs = modbus_srv.TestBench(tornado_srv.app.toDeviceQ, tornado_srv.app.toServerQ)
    mbs.daemon = True
    mbs.start()
    # scena = scenario.Scenario()

    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(tornado_srv.app())
    http_server.listen(options.port)
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "Listening on port:", options.port)
    time_start = time.monotonic()

    def modbus_listener():

        if time.monotonic() - tornado_srv.app.time_now > 2:
            tornado_srv.app.time_now = time.monotonic()
            livemin = int((time.monotonic() - time_start)/60)
            livesec = int(time.monotonic() - time_start - 60 * livemin)
            tornado_srv.app.toServerQ.put('{"LiveTime"  : {"value" : "%s мин %s сек"}}' % (livemin, livesec))

        if not tornado_srv.app.toServerQ.empty():
            result = tornado_srv.app.toServerQ.get()

            # # processing scenario
            # scena.readDeviceToServerMessage(result)
            # if not scena.toDeviceList.empty():
            #     tornado_srv.app.toDeviceQ.put(scena.toDeviceList.get())
            # if not scena.toServerList.empty():
            #     tornado_srv.app.toServerQ.put(scena.toServerList.get())
            # if not tornado_srv.app.toScenarioQ.empty():
            #     scena.readServerToScenarioMessage(tornado_srv.app.toScenarioQ.get())

            try:
                tmp = json.loads(result)
                if "MPCH_Indilogfile" in tmp:
                    tornado_srv.app.logfileIndic = tmp["MPCH_Indilogfile"]["value"]
                    return
                elif "MPCH_Cmdlogfile" in tmp:
                    tornado_srv.app.logfileCmd = tmp["MPCH_Cmdlogfile"]["value"]
                    return
            except json.decoder.JSONDecodeError as e: return

            for c in tornado_srv.app.clients:
                c.write_message(result)

    mainLoop = tornado.ioloop.IOLoop.instance()
    modbus   = tornado.ioloop.PeriodicCallback(modbus_listener, 10)
    modbus.start()
    mainLoop.start()






