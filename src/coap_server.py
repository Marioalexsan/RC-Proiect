# coap_server.py
# Implements the CoAP Server
import queue
import random
import threading
import socket
import time

import coap


# defineste exceptiile aparute in urma procesarii pachetelor Co-AP
class CoAPException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


# Defines the current state of a CoAP packet waiting to be sent
class CoAPState:
    def __init__(self):
        self.packet = CoAPPacket()
        self.attempts = 0
        self.cooldown = 0
        self.attempts_left = 0
        self.cooldown_left = 0


# Clasa pentru definirea unui pachet Co-AP cu toate campurile sale
class CoAPPacket:
    # Constructor
    def __init__(self):
        # CoAP stuff
        self.version = 0
        self.type = 0
        self.token_length = 0
        self.msg_class = 0
        self.msg_code = 0
        self.msg_id = 0
        self.options = {}
        self.payload = bytes(0)
        self.token = bytes(0)

        # Extra stuff
        self.addr = ('127.0.0.1', 5683)
        return

    # Initializeaza un pachet coap dintr-un sir de octeti
    # Parsarea este facuta dupa RFC7252
    def parse(self, data, addr):
        if data is None:
            return

        bytecount = len(data)
        bytesdone = 0

        if bytecount < 4:
            raise CoAPException("Not a CoAP packet")

        # Header Base

        self.version = (0xC0 & data[0]) >> 6
        self.type = (0x30 & data[0]) >> 4
        self.token_length = 0x0F & data[0]
        self.msg_class = (data[1] >> 5) & 0x07
        self.msg_code = data[1] & 0x1F
        self.msg_id = (data[2] << 8) | data[3]
        self.addr = addr

        bytesdone += 4

        # Tokens

        if bytecount < bytesdone + self.token_length:
            raise CoAPException("Bad packet")

        self.token = bytes(self.token_length)

        for i in range(0, self.token_length):
            self.token[i] = data[4 + i]

        bytesdone += self.token_length

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

            # Daca avem optiuni multiple, atunci delta este format din suma delta_precedent si delta_curent
            deltatouse = saveddelta + delta
            saveddelta += delta

            option = data[bytesdone:(bytesdone + length)]
            bytesdone += length

            # Pot fi si mai multe optiuni in unele cazuri, deci adaugam valorile parsate intr-o lista
            if deltatouse not in self.options:
                self.options[deltatouse] = []
            self.options[deltatouse].append(option)

        # The rest of the message is just payload, add it to packet
        # restule mesajului reprezinta date, adaugam la packet

        self.payload = data[bytesdone:bytecount]

        return

    # Functie de convertire a unui pachet coap la un sir de octeti / operatiunea inversa parsarii
    def tobytes(self):
        # Write base header
        data = [
            ((0x3 & self.version) << 6) | ((0x3 & self.type) << 4) | (0xF & self.token_length),
            ((self.msg_class & 0x7) << 5) | (self.msg_code & 0x1F), (self.msg_id & 0xFF00) >> 8,
            (self.msg_id & 0x00FF)
        ]

        # Write token (if any)

        for i in range(0, self.token_length):
            data.append(self.token[i])

        # Write options

        saveddelta = 0

        options = sorted(self.options.items(), key=lambda item: item[0])

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

        if self.payload is not None and len(self.payload) > 0:
            data.append(0xFF)  # Payload marker

            for i in range(0, len(self.payload)):
                data.append(self.payload[i])

        return bytes(data)

    # Functie de reprezentare scrisa a pachetului
    def __str__(self):
        text = "Version: {0}\n" \
               "Type: {1}\n" \
               "Class: {2}\n" \
               "Code: {3}\n" \
               "Message ID: {4}\n" \
               "Option count: {5}\n" \
            .format(self.version, self.type, self.msg_class, self.msg_code, self.msg_id, len(self.options))

        for pair in self.options.items():
            text += "  {0} =\n".format(pair[0])
            for option in pair[1]:
                text += "    * {0}\n".format(option.decode("utf-8"))

        text += 'Payload: {0}\n'.format(self.payload.decode("utf-8"))

        return text


# Clasa pentru definirea unui server Co-AP
class CoAPServer:
    # Constructor
    def __init__(self):
        self.ip = '127.0.0.1'  # Loopback IP
        self.port = 5683  # CoAP Port
        self.thread = None  # Socket's dedicated process
        self.event = threading.Event()  # Used to signal that process should stop
        self.sock = None  # The socket
        self.__current_id = 225
        self.__send_storage = []
        self.__last_update = 0

        # Msg Callback dictionary stores callbacks that are called for specific message codes
        self.msg_callbacks = {}

        return

    def setcallback(self, msg_class, msg_code, callback):
        if not callable(callback):
            raise Exception

        self.msg_callbacks[(msg_class, msg_code)] = callback

        return

    # Functie de pornire a serverului
    # Creeaza un socket de tipul UDP si creeaza un thread pentru citirea mesajulor
    def start(self):
        if self.sock is not None:
            return

        self.__last_update = time.time()
        self.event.clear()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP
        self.sock.bind((self.ip, self.port))
        self.thread = threading.Thread(target=self.__threadloop)
        self.thread.start()  # Start receive loop
        print("Started CoAP server.")

        return

    # Threadul pornit de server asteapta mesajele din aces loop
    def __threadloop(self):
        data = None
        clienterr_default = (coap.MCLASS_CLIENT_ERROR, coap.MSG_BAD_REQUEST)
        servererr_default = (coap.MCLASS_SERVER_ERROR, coap.MSG_INTERNAL_SERVER_ERROR)

        while not self.event.is_set():
            now = time.time()
            time_delta = now - self.__last_update
            self.__last_update = now

            # Update messages in storage
            for state in self.__send_storage:
                state.send_cooldown -= time_delta

                if state.send_cooldown < 0:
                    if state.attempts_left <= 0:
                        # TODO: No ACK message received. Log the error
                        self.__send_storage.remove(state)
                    else:
                        state.attempts_left -= 1
                        self.__sendforreal(state.packet)

            # Receive messages
            try:
                self.sock.settimeout(0.1)  # Wait for this long for any data
                data, addr = self.sock.recvfrom(65527)  # Maximum data size for a UDP datagram
                packet = CoAPPacket()  # Try to convert to CoAP
                packet.parse(data, addr)

            except socket.timeout:
                continue

            except CoAPException as e:
                print('Got a message, but parse failed.')
                print('Exception message: {0}'.format(e))
                print('Message contents: {0}'.format(data))

                # FIXME: Send a reset message, maybe? -mario
                continue

            except Exception as e:
                print('Got a message, but parse failed due to an internal error.')
                print('Exception message: {0}'.format(e))

                # FIXME: Send a reset message, maybe? -mario
                continue

            msg_ok = False

            if (packet.msg_class, packet.msg_code) in self.msg_callbacks:
                msg_ok = True

            if msg_ok:
                # Activate message callback
                reply = self.msg_callbacks[(packet.msg_class, packet.msg_code)](packet)

                if reply is CoAPPacket:
                    self.send(reply)
            elif packet.msg_class == coap.MCLASS_CLIENT_ERROR and clienterr_default in self.msg_callbacks:
                self.msg_callbacks[clienterr_default](packet)
            elif packet.msg_class == coap.MCLASS_SERVER_ERROR and servererr_default in self.msg_callbacks:
                self.msg_callbacks[servererr_default](packet)
            else:
                # Send a generic server error

                reply = CoAPPacket()
                reply.version = 1
                reply.type = 1  # Not CON
                reply.token_length = 0
                reply.msg_class = 5
                reply.msg_code = 1  # 5.01 Not Implemented
                reply.msg_id = self.generate_id()
                reply.addr = packet.addr
                reply.payload = bytes("The message type received ({0}.{1}) is unsupported!"
                                      .format(packet.msg_class, packet.msg_code))
                self.send(reply)

        return

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

        rand = random.random()

        state = CoAPState()
        state.cooldown = coap.COMM_ACK_TIMEOUT * ((coap.COMM_ACK_RANDOM_FACTOR - 1) * rand + 1)
        state.attempts = coap.COMM_MAX_RETRANSMIT
        state.send_cooldown = 0
        state.attempts_left = state.attempts

        # Add to messages that need to be sent
        self.__send_storage += state

        return

    def __sendforreal(self, packet: CoAPPacket):
        if self.sock is None:
            return

        try:
            self.sock.sendto(packet.tobytes(), packet.addr)
        except Exception as e:
            print("Couldn't send packet due to exception {0}".format(e))

        return

    def __sendreset(self, addr, msgid):
        packet = CoAPPacket()
        packet.version = 1
        packet.type = 3  # Reset
        packet.msg_class = 0
        packet.msg_Code = 0
        packet.token_length = 0
        packet.addr = addr

        self.send(packet)

    def generate_id(self):
        msgid = self.__current_id
        self.__current_id += 1
        return msgid
