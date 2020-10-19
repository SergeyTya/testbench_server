import multiprocessing
import time
from threading import Timer

import modbus_srv
import tornado_srv
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

    mbs = modbus_srv.TestBench(tornado_srv.app.taskQ, tornado_srv.app.resultQ)
    mbs.daemon = True
    mbs.start()


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
            tornado_srv.app.resultQ.put('{"LiveTime"  : {"value" : "%s мин %s сек"}}' % (livemin, livesec))

        if not tornado_srv.app.resultQ.empty():
            result = tornado_srv.app.resultQ.get()

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

    def scenario__control():
        pass

    mainLoop = tornado.ioloop.IOLoop.instance()
    modbus = tornado.ioloop.PeriodicCallback(modbus_listener, 10)
    scenario = tornado.ioloop.PeriodicCallback(scenario__control, 100)
    scenario.start()
    modbus.start()
    mainLoop.start()






