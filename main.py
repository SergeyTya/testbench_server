import multiprocessing
import modbus_srv
import tornado_srv
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options

if __name__ == "__main__":

    mbs = modbus_srv.TestBench(tornado_srv.app.taskQ, tornado_srv.app.resultQ)
    mbs.daemon = True
    mbs.start()

    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(tornado_srv.app())
    http_server.listen(options.port)
    print("Listening on port:", options.port)


    def modbus_listener():
        if not tornado_srv.app.resultQ.empty():
            result = tornado_srv.app.resultQ.get()
            # print("sent result", result)
            for c in tornado_srv.app.clients:
                c.write_message(result)

    mainLoop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(modbus_listener, 10)
    scheduler.start()
    mainLoop.start()
