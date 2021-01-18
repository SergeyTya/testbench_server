import time
from telnetlib import Telnet
import lief

if __name__ == "__main__":

    binary = lief.parse("/home/sergey/eclipse-workspace/ref103prj/Debug/ref103prj.elf")
    for symb in binary.symbols:
        if symb.name == "test_int":
            print(symb)
            adr = hex(symb.value)

    # with Telnet('localhost', 4444) as tn:
    #     time.sleep(0.1)
    #     print(tn.read_very_eager().decode('ascii'))
    #
    #     req = bytearray(" mdw %s 1 \n" % adr, 'ascii')
    #     while True:
    #         tn.write(req)
    #         time.sleep(1)
    #         str = tn.read_very_eager().decode('ascii')
    #         print(str)
    #
    #     tn.close()
