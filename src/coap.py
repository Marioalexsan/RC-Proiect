# coap.py
# Implements the CoAP Server

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
        print("Started CoAP server.")
        return

    def threadloop(self):
        while not self.event.is_set():
            try:
                self.sock.settimeout(1)
                data, addr = self.sock.recvfrom(65527)
            except socket.timeout:
                continue
            self.queue.put((data, addr))
        return

    def getdata(self):
        if self.queue.empty():
            return None
        return self.queue.get()

    def stop(self):
        if self.sock is None:
            return

        self.event.set()
        self.thread.join()

        self.sock = None
        self.thread = None

        print("Stopped CoAP server.")
        return