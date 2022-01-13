# coap_server.py
# Implements the CoAP Server
import random
import select
from threading import Thread, Event, Semaphore
import time
from socket import *
from typing import Optional, Callable, Dict, List, Tuple, Any

from coap import *


# Defines the current state of a CoAP packet waiting to be sent
class PendingReply:
    def __init__(self):
        self.packet = Packet()
        self.attempts = 0
        self.wait_time = 0
        self.attempts_left = 0
        self.time_left = 0


# Clasa pentru definirea unui server Co-AP
class Server:
    # Initializes CoAP Server using default values for options
    def __init__(self):
        self.ip = ''
        self.port = 5683
        self.__thread: Optional[Thread] = None  # Update thread
        self.__stop_event = Event()  # Thread stops when this is set
        self.__stop_event.set()
        self.__mutex = Semaphore(1)
        self.__sock: Optional[socket] = None
        self.__next_msgid = 225
        self.__con_replies: List[PendingReply] = []
        self.__last_time = 0

        # Msg Callback dictionary stores callbacks that are called for specific message codes
        self.packet_receivers: Dict[Tuple[int, int], Callable[[Packet], Packet]] = {}

        # Used for handling replies that were lost
        self.on_reply_lost: Optional[Callable[[Packet], None]] = None

        # Used for logging purposes
        self.on_request_received: Optional[Callable[[Packet], None]] = None

        # Used for logging purposes
        self.on_reply_sent: Optional[Callable[[Packet], None]] = None

        # Configuration
        self.config: Dict[str, Any] = {
            'timeout': 0.1,
            'maxdatasize': 65527
        }

        return

    # Functie de pornire a serverului
    # Creeaza un socket de tipul UDP si creeaza un thread pentru citirea mesajelor
    def start(self):
        if self.__thread is not None:
            return

        # Prepare stuff
        self.__stop_event.clear()
        self.__last_time = time.time()

        # Create socket
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.bind((self.ip, self.port))

        # Start update thread
        self.__thread = Thread(target=self.__threadloop)
        self.__thread.start()

        print("Started CoAP server.")
        return

    def stop(self):
        if self.__thread is None:
            return

        # Stop update thread
        self.__stop_event.set()
        self.__thread.join()
        self.__thread = None

        # Stop network connections
        self.__sock.close()
        self.__sock = None

        print("Stopped CoAP server.")
        return

    def is_active(self):
        return self.__thread is not None

    def send(self, packet: Packet):
        if self.__thread is None:
            return

        # If message is of type CON, use retransmission
        # For other message types, send the packet now
        if packet.type == TYPE_CON:
            reply = PendingReply()
            reply.packet = packet
            reply.wait_time = COMM_ACK_TIMEOUT * ((COMM_ACK_RANDOM_FACTOR - 1) * random.random() + 1)
            reply.attempts = COMM_MAX_RETRANSMIT
            reply.send_cooldown = 0
            reply.attempts_left = reply.attempts

            self.__mutex.acquire()
            self.__con_replies += reply
            self.__mutex.release()
        else:
            self.__send_packet(packet)

        return

    def generate_id(self):
        msgid = self.__next_msgid
        self.__next_msgid += 1
        return msgid

    # The server's update thread
    # It receives requests, and manages pending CON replies
    def __threadloop(self):
        while not self.__stop_event.is_set():

            # Get elapsed time
            now = time.time()
            time_delta = now - self.__last_time
            self.__last_time = now

            # Update messages that are waiting for ACK replies
            # Messages that exceed MAX_RETRANSMIT sends are removed
            self.__mutex.acquire()

            for reply in self.__con_replies:
                reply.time_left -= time_delta

                if reply.time_left <= 0:
                    if reply.attempts_left > 0:
                        reply.attempts_left -= 1
                        reply.time_left += reply.wait_time * (2 ** (reply.attempts - reply.attempts_left))
                        self.__send_packet(reply.packet)
                    else:
                        self.__con_replies.remove(reply)
                        if callable(self.on_reply_lost):
                            self.on_reply_lost(reply.packet)

            self.__mutex.release()

            # Receive messages

            data = None

            try:
                self.__sock.settimeout(self.config['timeout'])

                packet = Packet()
                data, packet.addr = self.__sock.recvfrom(self.config['maxdatasize'])
                packet.parse(data)

                try:
                    if callable(self.on_request_received):
                        self.on_request_received(packet)
                except Exception as e:
                    print('On Request Received event threw an exception for some reason!')
                    print(e)

            except timeout:
                continue
            except ParseException as e:
                print('Got a message, but parse failed.')
                print('Exception message: {0}'.format(e))
                print('Message contents: {0}'.format(data))
                continue
            except Exception as e:
                print('Got a message, but parse failed due to an internal error.')
                print('Exception message: {0}'.format(e))
                continue

            # Stop retransmission for all (one?) packets that match the ACK's ID.
            if packet.type == TYPE_ACK or packet.type == TYPE_RESET:
                self.__mutex.acquire()
                self.__con_replies = [msg for msg in self.__con_replies if msg.id != packet.id]
                self.__mutex.release()

            # Ignore RESET messages - we don't do much with them
            if packet.type == TYPE_RESET:
                continue

            # EMPTY is not allowed. Intercept and reply with RESET EMPTY if packet is CON or ACK.
            if packet.code == MSG_EMPTY:
                if packet.type in [TYPE_CON, TYPE_NON]:
                    reply = make_reset(packet.id, bytes(0))
                    self.send(reply)
                continue

            # Check if we know how to parse the packet
            if packet.code in self.packet_receivers:
                try:
                    reply = self.packet_receivers[packet.code](packet)
                except Exception:
                    reply = Packet(packet.get_reply_type(), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
                    reply.payload = bytes('An unknown internal error happened!', 'utf-8')
                    reply.addr = packet.addr
                    self.send(reply)

                # If the receiver returned a reply, send it
                if isinstance(reply, Packet):
                    reply.addr = packet.get_reply_type()
                    reply.addr = packet.addr
                    self.send(reply)

                # No valid reply, send ACK INTERNAL ERROR if CON
                elif packet.type == TYPE_CON:
                    reply = Packet(TYPE_ACK, MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
                    reply.payload = bytes('An unknown internal error happened!', 'utf-8')
                    reply.addr = packet.addr
                    self.send(reply)

            # We can't parse this - we'll use a server error instead of a non-descriptive RESET
            else:
                reply = Packet(packet.get_reply_type(), MSG_NOT_IMPLEMENTED, packet.id, packet.token)
                reply.payload = bytes('Server does not support the request type', 'utf-8')
                reply.addr = packet.addr
                self.send(reply)

        return

    def __send_packet(self, packet: Packet):
        if self.__sock is None:
            raise

        try:
            self.__sock.sendto(packet.tobytes(), packet.addr)

            if callable(self.on_reply_sent):
                self.on_reply_sent(packet)
        except Exception as e:
            print("Couldn't send packet due to exception {0}".format(e))

        return
