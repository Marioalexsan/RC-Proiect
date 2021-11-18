# coap_parser.py
import os

from coap import *
import json


class CoAPParser:
    def __init__(self):
        self.__jsondecoder = json.JSONDecoder()
        self.__jsonencoder = json.JSONEncoder()
        self.server_root = "C:\\Users\\elena\\OneDrive\\Desktop\\Server"

    def onget(self, packet: CoAPPacket):
        # TODO: Implement this properly
        # TODO: What goes here: command "details", "open"
        try:
            data = self.__jsondecoder.decode(str(packet.payload))
            print("Received JSON: ", data)
        except json.JSONDecodeError:
            pass

        cmd = data["cmd"]
        path = data["path"]

        if cmd == "details":
            pass
        elif cmd == "open":
            pass
        else:
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
        path = data["path"]

        # verific daca am caractere ilegale in path
        illegal_characters = ['#', '%', '&', '{', '}', '\\', '$', '!', '\'',
                              '\"', ':', '<', '>', '*', '?', ' ', '/', '+', '|', '=']
        for i in illegal_characters:
            if illegal_characters[i] in path:
                print("Bad request")
                reply = CoAPPacket()
                reply.version = COAP_VERSION
                reply.type = TYPE_ACK
                reply.code = MSG_BAD_REQUEST
                reply.id = packet.id
                reply.token = packet.token
                reply.payload = bytes("File not created - Illegal characters found in path/ Path is invalid")

        path_folder = os.path.join(self.server_root, path)

        if cmd == "create":  # Process "create" command

            arg_type = data["type"]
            if arg_type == "file":
                # creez un fisier
                try:
                    result = open(path, mode='x')
                    print("Created file ", path)
                    reply = CoAPPacket()
                    reply.version = COAP_VERSION
                    reply.type = TYPE_ACK
                    reply.code = MSG_CREATED
                    reply.id = packet.id
                    reply.token = packet.token
                    reply.payload = bytes(self.__jsonencoder.encode({'client_cmd': 'create',
                                                                     'status': 'created'
                                                                     }))
                    return reply
                except OSError as e:
                    print("Bad request")
                    reply = CoAPPacket()
                    reply.version = COAP_VERSION
                    reply.type = TYPE_ACK
                    reply.code = MSG_BAD_REQUEST
                    reply.id = packet.id
                    reply.token = packet.token
                    reply.payload = bytes("File not created")
                    return reply
                finally:
                    result.close()

            elif arg_type == "folder":
                # creez un folder
                try:
                    path_folder = os.path.join(self.server_root, path)
                    os.mkdir(path_folder)
                    print("Created file ", path)
                    reply = CoAPPacket()
                    reply.version = COAP_VERSION
                    reply.type = TYPE_ACK
                    reply.code = MSG_CREATED
                    reply.id = packet.id
                    reply.token = packet.token
                    reply.payload = bytes(self.__jsonencoder.encode({'client_cmd': 'create',
                                                                     'status': 'created'
                                                                     }))
                    return reply
                except OSError as e:
                    # in cazul in care deja exista, ma duce in eroarea FileExistsError
                    if e == 'FileExistsError':
                        print("Already exists", path_folder)
                        reply = CoAPPacket()
                        reply.version = COAP_VERSION
                        reply.type = TYPE_ACK
                        reply.code = MSG_CREATED
                        reply.id = packet.id
                        reply.token = packet.token
                        reply.payload = bytes(self.__jsonencoder.encode({'client_cmd': 'create',
                                                                         'status': 'existed'
                                                                         }))
                        return reply
                    # Tratare caz Bad Request
                    print("Bad request")
                    reply = CoAPPacket()
                    reply.version = COAP_VERSION
                    reply.type = TYPE_ACK
                    reply.code = MSG_BAD_REQUEST
                    reply.id = packet.id
                    reply.token = packet.token
                    reply.payload = bytes("Folder not created")  # 4.03 Forbidden
                    return reply
            else:  # type not recognised, send 4.00
                reply = CoAPPacket()
                reply.version = COAP_VERSION
                reply.type = TYPE_ACK
                reply.code = MSG_BAD_REQUEST
                reply.id = packet.id
                reply.token = packet.token
                reply.payload = bytes("Type not recognised")
                return reply
        elif cmd == "save":
            pass  # Process "save"
        elif cmd == "delete": #process delete command

            arg_type = data["type"]

            if arg_type == "file":
                if os.path.exists(path_folder):
                    if os.path.isfile(path_folder):
                        # sterg un fisier
                        try:
                            os.remove(path_folder)
                            print("Deleted file ", path)
                            reply = CoAPPacket()
                            reply.version = COAP_VERSION
                            reply.type = TYPE_ACK
                            reply.code = MSG_DELETED
                            reply.id = packet.id
                            reply.token = packet.token
                            reply.payload = bytes(self.__jsonencoder.encode({'client_cmd': 'delete',
                                                                             'status': 'deleted file'
                                                                             }))
                            return reply
                        except OSError as e:  # tratare eroare ce poate aparea la remove
                            if e == 'FileNotFoundError':
                                print("File was not found", path_folder)
                                reply = CoAPPacket()
                                reply.version = COAP_VERSION
                                reply.type = TYPE_ACK
                                reply.code = MSG_BAD_REQUEST
                                reply.id = packet.id
                                reply.token = packet.token
                                reply.payload = bytes("File not deleted")
                                return reply
                    else:
                        print("File ", path, " does not exist")
                        return
                else:
                    print("File does not exist")
                    return

            elif arg_type == "folder":
                # sterg directrul dat
                if os.path.exists(path_folder):
                    try:
                        os.rmdir(path_folder)
                        print("Deleted directory ", path)
                        reply = CoAPPacket()
                        reply.version = COAP_VERSION
                        reply.type = TYPE_ACK
                        reply.code = MSG_DELETED
                        reply.id = packet.id
                        reply.token = packet.token
                        reply.payload = bytes(self.__jsonencoder.encode({'client_cmd': 'delete',
                                                                         'status': 'deleted directory'
                                                                         }))
                        return reply
                    except OSError as e:
                        #in cazul in care nu exista, tratez eroarea FileNotFoundError
                        print("Bad request - Directory is not found or contains files", path_folder)
                        reply = CoAPPacket()
                        reply.version = COAP_VERSION
                        reply.type = TYPE_ACK
                        reply.code = MSG_BAD_REQUEST
                        reply.id = packet.id
                        reply.token = packet.token
                        reply.payload = bytes(self.__jsonencoder.encode({'client_cmd': 'delete',
                                                                         'status': 'MISSING directory'
                                                                         }))
                        return reply
                else: #4,04 Not Found
                    reply = CoAPPacket()
                    reply.version = COAP_VERSION
                    reply.type = TYPE_ACK
                    reply.code = MSG_BAD_REQUEST
                    reply.id = packet.id
                    reply.token = packet.token
                    reply.payload = bytes("Bad Request - Directory not found")
                    return reply
            else:
                print("Directory ", path, " does not exist")


        elif cmd == "rename":
            pass  # process rename
        elif cmd == "move":
            pass  # process move
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

        cmd = data["cmd"]
        path = data["path"]
        type = data["type"]

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
