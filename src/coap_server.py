# coap_server.py
# Implements the CoAP Server
import random
import threading
import socket
import time
from coap import *


# Defines the current state of a CoAP packet waiting to be sent
class PacketState:
    def __init__(self):
        self.packet = CoAPPacket()
        self.attempts = 0
        self.cooldown = 0
        self.attempts_left = 0
        self.cooldown_left = 0


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

    def stop(self):
        if self.__sock is None:
            return

        self.__stop_called.set()  # Tell process to stop
        self.__thread.join()  # Wait for process to stop
        self.__sock = None
        self.__thread = None
        print("Stopped CoAP server.")

        return

    def is_active(self):
        return self.__sock is not None

    def send(self, packet: CoAPPacket):
        if self.__sock is None:
            return

        if packet.type == TYPE_CON:
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

    def generate_id(self):
        msgid = self.__current_id
        self.__current_id += 1
        return msgid

    # Threadul pornit de server asteapta mesajele din aces loop
    def __threadloop(self):
        data = None

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

            if packet.code in self.on_receive:
                reply = self.on_receive[packet.code](packet)

                if reply is CoAPPacket:
                    reply.addr = packet.addr
                    self.send(reply)
            else:
                # Send a generic server error

                reply = make_not_implemented(packet.id)
                reply.addr = packet.addr
                self.send(reply)

        return

    def __send_packet(self, packet: CoAPPacket):
        if self.__sock is None:
            return

        try:
            self.__sock.sendto(packet.tobytes(), packet.addr)
        except Exception as e:
            print("Couldn't send packet due to exception {0}".format(e))

        return
