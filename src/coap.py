# coap.py
# Implements the CoAP Server
import queue
import threading
import socket


# defineste exceptiile aparute in urma procesarii pachetelor Co-AP
class CoAPException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)

#clasa pentru definirea unui pachet Co-AP cu toate campurile sale
class CoAPPacket:
    #constructor
    def __init__(self):
        self.mversion = 0
        self.mtype = 0
        self.mtkl = 0
        self.mclass = 0
        self.mcode = 0
        self.mid = 0
        self.addr = ('127.0.0.1', 5683)
        self.moptions = {}
        self.mpayload = bytes(0)
        self.token = bytes(0)

    #initializeaza un pachet coap dintr-un sir de octeti
    #parsarea este facuta dupa RFC7252
    def parse(self, data, addr):
        if data is None:
            return

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

            bytesdone += 1

            if delta == 0xF and length == 0xF:
                break  # Payload marker found

            if delta == 13:  # Delta extended with 1 byte
                delta = data[bytesdone] + 13
                bytesdone += 1
            elif delta == 14:  # Delta extended with 2 bytes
                delta = (data[bytesdone] << 8) + data[bytesdone + 1] + 269
                bytesdone += 2

            if length == 13:  # Length extended with 1 byte
                length = data[bytesdone] + 13
                bytesdone += 1
            elif length == 14:  # Length extended with 2 bytes
                length = (data[bytesdone] << 8) + data[bytesdone + 1] + 269
                bytesdone += 2

            #daca avem optiuni multiple, atunci delta este format din suma delta_precedent si delta_curent
            # If we have multiple options, then
            # true delta is formed by adding previous deltas
            deltatouse = saveddelta + delta
            saveddelta += delta

            option = data[bytesdone:(bytesdone + length)]
            bytesdone += length

            #pot fi si mai multe optiuni in unele cazuri, deci adaugam valorile parsate intr-o lista
            # There can be multiple options of the same delta, too
            # So we add the parsed values to a list
            if deltatouse not in self.moptions:
                self.moptions[deltatouse] = []
            self.moptions[deltatouse].append(option)

        # The rest of the message is just payload, add it to packet
        # restule mesajului reprezinta date, adaugam la packet

        self.mpayload = data[bytesdone:bytecount]

        return

    #functie de convertire a unui pachet coap la un sir de octeti / operatiunea inversa parsarii
    def tobytes(self):
        data = []

        # Write base header

        data.append(((0x3 & self.mversion) << 6) | ((0x3 & self.mtype) << 4) | (0xF & self.mtkl))
        data.append(((self.mclass & 0x7) << 5) | (self.mcode & 0x1F))
        data.append((self.mid & 0xFF00) >> 8)
        data.append((self.mid & 0x00FF))

        # Write token (if any)

        for i in range(0, self.mtkl):
            data.append(self.token[i])

        # Write options

        saveddelta = 0

        options = sorted(self.moptions.items(), key=lambda item: item[0])

        for pair in options:
            deltatouse = pair[0] - saveddelta
            saveddelta += deltatouse

            length = len(pair[1])

            firstbyte = 0

            # Write first byte

            if deltatouse <= 12:
                firstbyte |= (0xF & deltatouse) << 4
            elif deltatouse <= 268:
                firstbyte |= 13 << 4
            else:
                firstbyte |= 14 << 4

            if length <= 12:
                firstbyte |= (0xF & length)
            elif length <= 268:
                firstbyte |= 13
            else:
                firstbyte |= 14

            data.append(firstbyte)

            # Write extended option info

            if deltatouse >= 269:
                data.append((0xFF00 & (deltatouse - 269)) >> 4)
                data.append(0xFF & (deltatouse - 269))
            elif deltatouse >= 13:
                data.append(0xFF & (deltatouse - 13))

            if length >= 269:
                data.append((0xFF00 & (length - 269)) >> 4)
                data.append(0xFF & (length - 269))
            elif length >= 13:
                data.append(0xFF & (length - 13))

            # Write the option itself

            for i in range(0, len(pair[1])):
                data.append(pair[1][i])

        if self.mpayload is not None and len(self.mpayload) > 0:
            data.append(0xFF)  # Payload marker

            for i in range(0, len(self.mpayload)):
                data.append(self.mpayload[i])

        return bytes(data)

    #functie de reprezentare scrisa a pachetului
    def __str__(self):
        text = "Version: {0}\n" \
               "Type: {1}\n" \
               "Class: {2}\n" \
               "Code: {3}\n" \
               "Message ID: {4}\n" \
               "Option count: {5}\n" \
            .format(self.mversion, self.mtype, self.mclass, self.mcode, self.mid, len(self.moptions))

        for pair in self.moptions.items():
            text += "  {0} =\n".format(pair[0])
            for option in pair[1]:
                text += "    * {0}\n".format(option.decode("utf-8"))

        text += 'Payload: {0}\n'.format(self.mpayload.decode("utf-8"))

        return text


#clasa pentru definirea unui server Co-AP
class CoAPServer:
    #constructor
    def __init__(self, onreceive=None):
        self.ip = '127.0.0.1'  # Loopback IP
        self.port = 5683  # CoAP Port
        self.thread = None  # Socket's dedicated process
        self.event = threading.Event()  # Used to signal that process should stop
        self.queue = queue.Queue()  # Used to get messages
        self.sock = None  # The socket
        self.onreceive = onreceive
        return

    #functie de pornire a serverului
    #creeaza un socket de tipul UDP si creeaza un thread pentru citirea mesajulor
    def start(self):
        if self.sock is not None:
            return
        self.event.clear()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP
        self.sock.bind((self.ip, self.port))
        self.thread = threading.Thread(target=self.__threadloop)
        self.thread.start()  # Start receive loop
        print("Started CoAP server.")
        return

    #threadul pornit de server asteapta mesajele din aces loop
    def __threadloop(self):
        data = None

        while not self.event.is_set():
            try:
                self.sock.settimeout(0.25)  # Wait for this long for any data
                data, addr = self.sock.recvfrom(65527)  # Maximum data size for a UDP datagram
                packet = CoAPPacket()  # Try to convert to CoAP
                packet.parse(data, addr)

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
        return self.queue.get()  # Returns coap packet

    def stop(self):
        if self.sock is None:
            return
        self.event.set()  # Tell process to stop
        self.thread.join()  # Wait for process to stop
        self.sock = None
        self.thread = None
        print("Stopped CoAP server.")
        return

    def send(self, packet: CoAPPacket):
        if self.sock is None:
            return

        try:
            self.sock.sendto(packet.tobytes(), packet.addr)
        except Exception as e:
            print("Couldn't send packet due to exception {0}".format(e))

        return
