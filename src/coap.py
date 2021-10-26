# CoAP Helper
# Purpose: Implements some easy-access methods
# for the Constrained Application Protocol
import multiprocessing
import socket


class COAPServer:
    def __init__(self):
        self.ip = '127.0.0.1'
        self.port = 5683
        self.thread = None
        self.event = multiprocessing.Event()
        self.queue = multiprocessing.Queue()
        self.sock = None
        return

    def start(self):
        if self.sock is not None:
            return

        self.event.clear()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))

        self.thread = multiprocessing.Process(target=self.threadloop)
        self.thread.start()

        return

    def threadloop(self):
        while not self.event.is_set():
            # 65527 + 8 (header) = 65535 bytes = max datagram size
            try:
                self.sock.settimeout(1)
                data, addr = self.sock.recvfrom(65527)
            except Exception:
                continue
            print('Got from {0}: {1}'.format(addr, data))
            self.queue.put((data, addr))
        return

    def getdata(self):
        if self.queue.empty():
            return None
        else:
            return self.queue.get()

    def stop(self):
        if self.sock is None:
            return

        print('Stopping server...')

        self.event.set()
        self.thread.join()

        self.sock = None
        self.thread = None

        print('Stopped server.')
        return