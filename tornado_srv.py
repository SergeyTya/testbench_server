import datetime
import json
import multiprocessing
import time

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.websocket
import os.path

from tornado import httputil
from tornado.options import define, options
import modbus_srv
import schn

define("port", default=8080, help="run on the given port", type=int)


class app(tornado.web.Application):

    clients = []
    input_names = []
    holding_names = []
    toDeviceQ = multiprocessing.Queue()
    toServerQ = multiprocessing.Queue()
    toScenarioQ = multiprocessing.Queue()
    logfileIndic = ""
    logfileCmd = ""
    time_now = time.monotonic()

    def __init__(self):
        handlers = [
            (r"/", self.MainHandler),
            (r"/save_mprm", self.SaveMpchParamHandler),
            (r"/ws", self.WebSocketHandler),
            (r"/statistics", self.StatHandler),
            (r"/statistics2", self.StatHandler2)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        try:
            # Читаем имена индкаторов
            with open('indi.json', 'r',
                      encoding='utf8'
                      ) as fh:
                app.input_names = json.load(fh)
            with open('prm.json', 'r',
                      encoding='Windows-1251'
                      ) as fh:
                app.holding_names = json.load(fh)
        except (
                json.decoder.JSONDecodeError,
                FileNotFoundError,
                UnicodeDecodeError
        ) as e:
            print(e)
        tornado.web.Application.__init__(self, handlers, **settings)


    class MainHandler(tornado.web.RequestHandler):
        def get(self):

            self.render(
                "index.html",
                input_names=app.input_names,
                holding_names=app.holding_names,
                logfile=app.logfileCmd,
                schn_iname=schn.schn_iname

            )

    class SaveMpchParamHandler(tornado.web.RequestHandler):
        def get(self):
            self.render("save_mprm.html")

    class StatHandler(tornado.web.RequestHandler):
        def get(self):
            self.render(
                "stati.html",
                logfile=app.logfileIndic,
                input_names=app.input_names,
            )

    class StatHandler2(tornado.web.RequestHandler):
        def get(self):
            self.render(
                "stati2.html",
                logfile=app.logfileCmd,
            )

    class WebSocketHandler(tornado.websocket.WebSocketHandler):
        def open(self):
            tmp = '{"CMD":"%s"}'
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "new connection", id(self))
            app.clients.append(self)
            app.toDeviceQ.put(tmp % modbus_srv.Commands.MPCH_Get_AllHoldings)
            app.toDeviceQ.put(tmp % modbus_srv.Commands.MPCH_Get_SlaveID)
            app.toDeviceQ.put(tmp % modbus_srv.Commands.MPCH_Get_Status)
            app.toDeviceQ.put(tmp % modbus_srv.Commands.Schn_getID)

        def on_message(self, message):
            #self.write_message('got message! ' + message )
            app.toDeviceQ.put(message)


        def on_close(self):
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " : ", "connection closed")
            app.clients.remove(self)




