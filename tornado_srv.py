import json
import multiprocessing

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.websocket
import os.path
from tornado.options import define, options
import modbus_srv

define("port", default=8080, help="run on the given port", type=int)


class app(tornado.web.Application):

    clients = []
    input_names = []
    holding_names = []
    taskQ = multiprocessing.Queue()
    resultQ = multiprocessing.Queue()

    def __init__(self):
        handlers = [
            (r"/", self.MainHandler),
            (r"/save_mprm", self.SaveMpchParamHandler),
            (r"/ws", self.WebSocketHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        try:
            # Читаем имена индкаторов
            with open('INDI.json', 'r',
                      encoding='utf8'
                      ) as fh:
                app.input_names = json.load(fh)
            with open('PRM.json', 'r',
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
                holding_names=app.holding_names
            )

    class SaveMpchParamHandler(tornado.web.RequestHandler):
        def get(self):
            self.render("save_mprm.html")

    class WebSocketHandler(tornado.websocket.WebSocketHandler):
        def open(self):
            tmp = '{"CMD":"%s"}'
            print("new connection", id(self))
            app.clients.append(self)
            app.taskQ.put(tmp % modbus_srv.Commands.MPCH_Get_AllHoldings)
            app.taskQ.put(tmp % modbus_srv.Commands.MPCH_Get_SlaveID)
            app.taskQ.put(tmp % modbus_srv.Commands.MPCH_Get_Status)

        def on_message(self, message):
            #self.write_message('got message! ' + message )
            app.taskQ.put(message)


        def on_close(self):
            print("connection closed")
            app.clients.remove(self)




