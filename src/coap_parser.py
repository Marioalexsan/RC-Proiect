# coap_parser.py
from coap import *
import json


class CoAPParser:
    def __init__(self):
        self.__jsondecoder = json.JSONDecoder()
        self.__jsonencoder = json.JSONEncoder()

    def onget(self, packet: CoAPPacket):
        # TODO: Implement this properly
        # TODO: What goes here: command "details", "open"
        try:
            data = self.__jsondecoder.decode(str(packet.payload))
            print("Received JSON: ", data)
        except json.JSONDecodeError:
            pass

        reply = CoAPPacket()
        reply.version = COAP_VERSION
        reply.type = TYPE_NON
        reply.code = MSG_CONTENT
        reply.token = packet.token
        reply.payload = self.__jsonencoder.encode({'lol': 0})
        return reply

    def onpost(self, packet: CoAPPacket):
        # TODO: Implement this properly
        # TODO: What goes here: commands "create", "save", "delete", "rename", "move"
        data = None
        try:
            data = self.__jsondecoder.decode(str(packet.payload))
            print("Received JSON: ", data)
        except json.JSONDecodeError:
            pass

        cmd = data["cmd"]
        path = data["execute_path"]

        if cmd == "create":
            pass  # Process "create" command
        elif cmd == "save":
            pass  # Process "save"
        else:
            pass  # Couldn't recognize command, send 4.00 Bad Request, with payload "Client sent an invalid command"

        reply = CoAPPacket()
        reply.version = COAP_VERSION
        reply.type = TYPE_NON
        reply.code = MSG_CHANGED
        reply.id = packet.id
        reply.token = packet.token
        reply.payload = self.__jsonencoder.encode({'lol': 1})
        return reply

    def onput(self, packet: CoAPPacket):
        # TODO: Implement this properly
        try:
            data = self.__jsondecoder.decode(str(packet.payload))
            print("Received JSON: ", data)
        except json.JSONDecodeError:
            pass

        payload = {'lol': 2}

        reply = CoAPPacket()
        reply.version = COAP_VERSION
        reply.type = TYPE_NON
        reply.code = MSG_CHANGED
        reply.id = packet.id
        reply.token = packet.token
        reply.payload = self.__jsonencoder.encode(payload)
        return reply

    def ondelete(self, packet: CoAPPacket):
        # TODO: Implement this properly
        try:
            data = self.__jsondecoder.decode(str(packet.payload))
            print("Received JSON: ", data)
        except json.JSONDecodeError:
            pass

        payload = {'lol': 3}

        reply = CoAPPacket()
        reply.version = COAP_VERSION
        reply.type = TYPE_NON
        reply.code = MSG_DELETED
        reply.id = packet.id
        reply.token = packet.token
        reply.payload = self.__jsonencoder.encode(payload)
        return reply

    def onsearch(self, packet: CoAPPacket):
        # TODO: Implement this properly
        try:
            data = self.__jsondecoder.decode(str(packet.payload))
            print("Received JSON: ", data)
        except json.JSONDecodeError:
            pass

        payload = {'lol': 8}

        reply = CoAPPacket()
        reply.version = COAP_VERSION
        reply.type = TYPE_NON
        reply.code = MSG_CONTENT
        reply.id = packet.id
        reply.token = packet.token
        reply.payload = self.__jsonencoder.encode(payload)
        return reply
