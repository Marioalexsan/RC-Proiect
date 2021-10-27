# coap.py
# Implements the CoAP Server
import queue
import threading
import socket


class CoAPException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class CoAPPacket:
    def __init__(self, data, addr):
        bytecount = len(data)
        bytesdone = 0

        if bytecount < 4:
            raise CoAPException("Not a CoAP packet")

        # Header Base

        self.mversion = (0xC0 & data[0]) >> 6
        self.mtype = (0x30 & data[0]) >> 4
        self.mtkl = 0x0F & data[0]
        self.mclass = (data[1] >> 5) & 0x07
        self.mcode = data[1] & 0x1F
        self.mid = (data[2] << 8) | data[3]
        self.addr = addr
        self.moptions = {}
        self.mpayload = bytes(0)

        bytesdone += 4

        # Tokens

        if bytecount < bytesdone + self.mtkl:
            raise CoAPException("Bad packet")

        self.token = bytes(self.mtkl)

        for i in range(0, self.mtkl):
            self.token[i] = data[4 + i]

        bytesdone += self.mtkl

        # Options

        saveddelta = 0

        while True:
            if bytecount == bytesdone:
                return  # End of message found

            delta = (0xF0 & data[bytesdone]) >> 4
            length = 0x0F & data[bytesdone]

            if delta == 0xF and length == 0xF:
                bytesdone += 1  # Payload marker found
                break

            if delta == 13:  # Delta extended with 1 byte
                delta += data[bytesdone + 1]
                bytesdone += 1
            elif delta == 14:  # Delta extended with 2 bytes
                delta += (data[bytesdone + 1] << 8) + data[bytesdone + 2]
                bytesdone += 2

            if length == 13:  # Length extended with 1 byte
                length += data[bytesdone + 1]
                bytesdone += 1
            elif length == 14:  # Length extended with 2 bytes
                length += (data[bytesdone + 1] << 8) + data[bytesdone + 2]
                bytesdone += 2

            # If we have multiple options, then
            # true delta is formed by adding previous deltas
            deltatouse = saveddelta + delta
            saveddelta += delta

            option = data[bytesdone:(bytesdone + length)]

            # There can be multiple options of the same delta, too
            # So we add the parsed values to a list
            if self.moptions[deltatouse] is None:
                self.moptions[deltatouse] = []
            self.moptions[deltatouse].append(option)

        # The rest of the message is just payload, add it to packet

        self.mpayload = data[bytesdone:bytecount]

        return

    def __str__(self):
        text = "Version: {0}\n" \
               "Type: {1}\n" \
               "Class: {2}\n" \
               "Code: {3}\n" \
               "Message ID: {4}\n" \
               "Option count: {5}" \
            .format(self.mversion, self.mtype, self.mclass, self.mcode, self.mid, len(self.moptions))

        return text


class CoAPServer:
    def __init__(self, onreceive=None):
        self.ip = '127.0.0.1'  # Loopback IP
        self.port = 5683  # CoAP Port
        self.thread = None  # Socket's dedicated process
        self.event = threading.Event()  # Used to signal that process should stop
        self.queue = queue.Queue()  # Used to get messages
        self.sock = None  # The socket
        self.onreceive = onreceive
        return

    def start(self):
        if self.sock is not None:
            return
        self.event.clear()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP
        self.sock.bind((self.ip, self.port))
        self.thread = threading.Thread(target=self.threadloop)
        self.thread.start()  # Start receive loop
        print("Started CoAP server.")
        return

    def threadloop(self):
        data = None

        while not self.event.is_set():
            try:
                self.sock.settimeout(0.25)  # Listen for a second each time
                data, addr = self.sock.recvfrom(65527)  # Maximum data size for a UDP datagram
                packet = CoAPPacket(data, addr)  # Try to convert to CoAP

            except socket.timeout:
                continue
            except CoAPException as e:
                print('Got a message, but parse failed.')
                print('Exception message: {0}'.format(e))
                print('Message contents: {0}'.format(data))
                continue
            except Exception as e:
                print('Got a message, but parse failed due to an internal error.')
                print('Exception message: {0}'.format(e))
                continue

            if self.onreceive is not None:
                self.onreceive(packet)
            else:
                self.queue.put(packet)
        return

    def getdata(self):
        if self.queue.empty():
            return None
        return self.queue.get()  # Returns (bytes, address)

    def stop(self):
        if self.sock is None:
            return
        self.event.set()  # Tell process to stop
        self.thread.join()  # Wait for process to stop
        self.sock = None
        self.thread = None
        print("Stopped CoAP server.")
        return
