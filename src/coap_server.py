# coap_server.py
# Implements the CoAP Server
import random
import threading
import socket
import time
from coap import *


# defineste exceptiile aparute in urma procesarii pachetelor Co-AP
class CoAPException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


# Defines the current state of a CoAP packet waiting to be sent
class PacketState:
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
    def parse(self, data):
        if data is None:
            raise CoAPException("No data provided")

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
        self.__thread = None  # Socket's dedicated process
        self.__stop_called = threading.Event()  # Used to signal that process should stop
        self.__sock = None  # The socket
        self.__current_id = 225
        self.__messages_sending = []
        self.__last_update_at = 0

        # Msg Callback dictionary stores callbacks that are called for specific message codes
        self.on_receive = {}
        self.on_ack_fail = None

        # Configuration
        self.cfg_recvtimeout = 0.1  # In seconds
        self.cfg_maxdatasize = 65527  # Maximum data size for a UDP datagram

        return

    # Functie de pornire a serverului
    # Creeaza un socket de tipul UDP si creeaza un thread pentru citirea mesajulor
    def start(self):
        if self.__sock is not None:
            return

        self.__last_update_at = time.time()
        self.__stop_called.clear()
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP
        self.__sock.bind((self.ip, self.port))
        self.__thread = threading.Thread(target=self.__threadloop)
        self.__thread.start()  # Start receive loop
        print("Started CoAP server.")

        return

    # Threadul pornit de server asteapta mesajele din aces loop
    def __threadloop(self):
        data = None
        default_client_error = (MCLASS_CLIENT_ERROR, MSG_BAD_REQUEST)
        default_server_error = (MCLASS_SERVER_ERROR, MSG_INTERNAL_SERVER_ERROR)

        while not self.__stop_called.is_set():
            now = time.time()
            time_delta = now - self.__last_update_at
            self.__last_update_at = now

            # Update messages that are waiting for ACK replies
            # Messages that exceed MAX_RETRANSMIT sends are removed
            for state in self.__messages_sending:
                state.cooldown_left -= time_delta

                if state.cooldown_left <= 0:
                    if state.attempts_left > 0:
                        state.attempts_left -= 1
                        state.cooldown_left += state.cooldown * (2 ** (state.attempts - state.attempts_left))
                        self.__send_packet(state.packet)
                    else:
                        self.__messages_sending.remove(state)
                        if callable(self.on_ack_fail):
                            self.on_ack_fail(state.packet)

            # Receive messages
            # FIXME: Send a reset message for non-timeout exceptions? -mario
            try:
                self.__sock.settimeout(self.cfg_recvtimeout)
                data, addr = self.__sock.recvfrom(65527)
                packet = CoAPPacket()
                packet.addr = addr
                packet.parse(data)
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

            msg_understood = (packet.msg_class, packet.msg_code) in self.on_receive
            is_client_error = packet.msg_class == MCLASS_CLIENT_ERROR
            is_server_error = packet.msg_class == MCLASS_SERVER_ERROR

            if msg_understood:
                reply = self.on_receive[(packet.msg_class, packet.msg_code)](packet)

                if reply is CoAPPacket:
                    self.send(reply)
            elif is_client_error and default_client_error in self.on_receive:
                self.on_receive[default_client_error](packet)
            elif is_server_error and default_server_error in self.on_receive:
                self.on_receive[default_server_error](packet)
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
        if self.__sock is None:
            return

        self.__stop_called.set()  # Tell process to stop
        self.__thread.join()  # Wait for process to stop
        self.__sock = None
        self.__thread = None
        print("Stopped CoAP server.")

        return

    def send(self, packet: CoAPPacket):
        if self.__sock is None:
            return

        if packet.type == MTYPE_CON:
            # We may need to send this multiple times until we get an ACK message
            rand = random.random()

            state = PacketState()
            state.packet = packet
            state.cooldown = COMM_ACK_TIMEOUT * ((COMM_ACK_RANDOM_FACTOR - 1) * rand + 1)
            state.attempts = COMM_MAX_RETRANSMIT
            state.send_cooldown = 0
            state.attempts_left = state.attempts

            self.__messages_sending += state
        else:
            # Send it right away
            self.__send_packet(packet)

        return

    def __send_packet(self, packet: CoAPPacket):
        if self.__sock is None:
            return

        try:
            self.__sock.sendto(packet.tobytes(), packet.addr)
        except Exception as e:
            print("Couldn't send packet due to exception {0}".format(e))

        return

    def __sendreset(self, addr, msgid):
        packet = CoAPPacket()
        packet.version = 1
        packet.type = 3  # Reset
        packet.msg_class = 0
        packet.msg_Code = 0
        packet.msg_id = msgid
        packet.token_length = 0
        packet.addr = addr

        self.send(packet)

    def generate_id(self):
        msgid = self.__current_id
        self.__current_id += 1
        return msgid
