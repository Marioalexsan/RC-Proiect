# coap_parser.py
import os

from coap import *
import json
import stat
from pathlib import Path


class Parser:
    def __init__(self):
        self.__jsondecoder = json.JSONDecoder()
        self.__jsonencoder = json.JSONEncoder()
        self.server_root = 'server_files/'

        self.get_commands = {
            'open': self.command_open,
            'details': self.command_details
        }

        self.post_commands = {
            'create': self.command_create,
            'delete': self.command_delete,
            'save': self.command_save,
            'rename': self.command_rename,
            'move': self.command_move,
        }

        return

    # Validates paths taken from client requests
    def __validate_path(self, path: str):
        if path is None:
            return None

        if os.path.isabs(path):
            return None

        root = os.path.join(os.getcwd(), self.server_root)
        root = os.path.normcase(root)
        root = os.path.normpath(root)
        root = root.replace('\\', '/')

        path = os.path.join(root, path)
        path = os.path.normcase(path)
        path = os.path.normpath(path)
        path = path.replace('\\', '/')

        if not path.startswith(root):
            return None

        return path

    def onget(self, packet: Packet):
        # TODO: Implement this properly
        # TODO: What goes here: command 'details', 'open'

        payload = packet.payload.decode('utf-8')

        data = None
        try:
            data = self.__jsondecoder.decode(payload)
        except json.JSONDecodeError:
            pass

        server_path = self.__validate_path(data['path'])

        if data['cmd'] is None or data['path'] is None:
            print('Received a malformatted request')
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('Received a malformatted request', 'utf-8')
            return reply

        if server_path is None:
            print('Received an invalid path.')
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('The path requested is invalid, or access has been denied by the server.', 'utf-8')
            return reply

        if data['cmd'] in self.get_commands:
            return self.get_commands[data['cmd']](packet, data, server_path)
        else:  # Couldn't recognize command, send 4.00 Bad Request, with payload 'Client sent an invalid command'
            print('The request command was invalid')
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('The request command was invalid', 'utf-8')
            return reply

    def onpost(self, packet: Packet):
        # TODO: Implement this properly
        # TODO: What goes here: commands 'create', 'save', 'delete', 'rename', 'move'

        payload = packet.payload.decode('utf-8')

        data = None
        try:
            data = self.__jsondecoder.decode(payload)
        except json.JSONDecodeError:
            pass

        server_path = self.__validate_path(data['path'])

        if data['cmd'] is None or data['path'] is None:
            print('Received a malformatted request')
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('Received a malformatted request', 'utf-8')
            return reply

        if server_path is None:
            print('Received an invalid path.')
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('The path requested is invalid, or access has been denied by the server.', 'utf-8')
            return reply

        if data['cmd'] in self.post_commands:
            return self.post_commands[data['cmd']](packet, data, server_path)
        else:  # Couldn't recognize command, send 4.00 Bad Request, with payload 'Client sent an invalid command'
            print('The request command was invalid')
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('The request command was invalid', 'utf-8')
            return reply

    def onput(self, packet: Packet):
        # TODO: Implement this properly
        reply = make_not_implemented(packet.id, packet.token)
        reply.payload = bytes('Server does not support this command (yet)', 'utf-8')
        return reply

    def ondelete(self, packet: Packet):
        # TODO: Implement this properly
        reply = make_not_implemented(packet.id, packet.token)
        reply.payload = bytes('Server does not support this command (yet)', 'utf-8')
        return reply

    def onsearch(self, packet: Packet):
        # TODO: Implement this properly
        reply = make_not_implemented(packet.id, packet.token)
        reply.payload = bytes('Server does not support this command (yet)', 'utf-8')
        return reply

    def command_create(self, packet: Packet, p_data, server_path):
        if p_data['type'] is None or p_data['type'] not in ['file', 'folder']:  # type not recognised, send 4.00
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('Requested FS object type is invalid', 'utf-8')
            return reply

        if p_data['type'] == 'file':  # creez un fisier
            try:
                with open(server_path, mode='x'):
                    data = {'client_cmd': 'create', 'status': 'created'}

                    reply = Packet(get_reply_type(packet), MSG_CREATED, packet.id, packet.token)
                    reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')

                    print('Created file', server_path)
                    return reply

            except FileExistsError:
                data = {'client_cmd': 'create', 'status': 'exists'}

                reply = Packet(get_reply_type(packet), MSG_CREATED, packet.id, packet.token)
                reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')

                print('File already exists', server_path)
                return reply

            except OSError:
                print('Failed to create file', server_path)

                reply = Packet(get_reply_type(packet), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
                reply.payload = bytes('File not created', 'utf-8')
                return reply

        elif p_data['type'] == 'folder':  # creez un folder
            try:
                os.mkdir(server_path)

                data = {'client_cmd': 'create', 'status': 'created'}

                reply = Packet(get_reply_type(packet), MSG_CREATED, packet.id, packet.token)
                reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')

                print('Created folder', server_path)
                return reply

            except FileExistsError:  # in cazul in care deja exista, ma duce in eroarea FileExistsError
                data = {'client_cmd': 'create', 'status': 'existed'}

                reply = Packet(get_reply_type(packet), MSG_CREATED, packet.id, packet.token)
                reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')

                print('Folder exists', server_path)
                return reply

            except OSError:  # Tratare caz Bad Request
                reply = Packet(get_reply_type(packet), MSG_FORBIDDEN, packet.id, packet.token)
                reply.payload = bytes('File system error during folder creation', 'utf-8')  # 4.03 Forbidden

                print('Error when creating folder', server_path)
                return reply
        return None

    def command_delete(self, packet, p_data, server_path):
        if not os.path.exists(server_path):
            reply = Packet(get_reply_type(packet), MSG_NOT_FOUND, packet.id, packet.token)
            reply.payload = bytes('Object at given path does not exist', 'utf-8')

            print('Delete path does not exist')
            return reply
        try:
            data = None
            if os.path.isfile(server_path):  # sterg un fisier
                os.remove(server_path)
                data = {'client_cmd': 'delete', 'status': 'deleted file'}
            elif os.path.isdir(server_path):
                os.rmdir(server_path)
                data = {'client_cmd': 'delete', 'status': 'deleted folder'}
            else:
                reply = Packet(get_reply_type(packet), MSG_FORBIDDEN, packet.id, packet.token)
                reply.payload = bytes('Object given is neither file nor folder', 'utf-8')

                print('bject given is neither file nor folder')
                return reply

            print('Deleted object ', server_path)

            reply = Packet(get_reply_type(packet), MSG_DELETED, packet.id, packet.token)
            reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')
            return reply

        except OSError:  # tratare eroare ce poate aparea la remove
            reply = Packet(get_reply_type(packet), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
            reply.payload = bytes('Failed to delete object')

            print('Encountered a problem when deleting object', server_path)
            return reply

    def command_open(self, packet, p_data, server_path):
        if not os.path.exists(server_path):
            reply = Packet(get_reply_type(packet), MSG_NOT_FOUND, packet.id, packet.token)
            reply.payload = bytes('The given path does not exist', 'utf-8')

            print('Path does not exist')
            return reply

        if not os.path.isfile(server_path):
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('The given path is not a file', 'utf-8')

            print('Path is not a file')
            return reply
        try:
            with open(server_path, 'r') as file:
                contents = file.read(65527)
                data = {'client_cmd': 'open', 'response': contents}

                reply = Packet(get_reply_type(packet), MSG_CONTENT, packet.id, packet.token)
                reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')
                return reply

        except OSError:
            reply = Packet(get_reply_type(packet), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
            reply.payload = bytes('Failed to open file')

            print('Encountered a problem while opening file', server_path)

    def command_save(self, packet, p_data, server_path):
        if not p_data['content']:
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('No content was provided', 'utf-8')

            print('Client sent a save command without content')
            return reply

        if not os.path.exists(server_path):
            reply = Packet(get_reply_type(packet), MSG_NOT_FOUND, packet.id, packet.token)
            reply.payload = bytes('The given path does not exist', 'utf-8')

            print('Path does not exist')
            return reply

        if not os.path.isfile(server_path):
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('The given path is not a file', 'utf-8')

            print('Path is not a file')
            return reply
        try:
            with open(server_path, 'w') as file:
                file.write(p_data['content'])
                data = {'client_cmd': 'open', 'status': 'modified'}

                reply = Packet(get_reply_type(packet), MSG_CHANGED, packet.id, packet.token)
                reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')
                return reply

        except OSError:
            reply = Packet(get_reply_type(packet), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
            reply.payload = bytes('Failed to open file')

            print('Encountered a problem while opening file', server_path)

    def command_rename(self, packet, p_data, server_path: str):
        if not p_data['name'] or '/' in p_data['name']:
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('No new name was provided, or name is invalid', 'utf-8')

            print('Client sent a rename command without the new name, or name is invalid')
            return reply

        if not os.path.exists(server_path):
            reply = Packet(get_reply_type(packet), MSG_NOT_FOUND, packet.id, packet.token)
            reply.payload = bytes('The given path does not exist', 'utf-8')

            print('Path does not exist')
            return reply

        new_path = server_path[:(server_path.rindex('/') + 1)] + p_data['name']

        if os.path.exists(new_path):
            reply = Packet(get_reply_type(packet), MSG_FORBIDDEN, packet.id, packet.token)
            reply.payload = bytes('An object with that name already exists', 'utf-8')

            print('An object with that name already exists')
            return reply

        try:
            os.rename(server_path, new_path)
            data = {'client_cmd': 'rename', 'status': 'renamed'}

            reply = Packet(get_reply_type(packet), MSG_CHANGED, packet.id, packet.token)
            reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')

            print('Renamed object', server_path, 'to', new_path)
            return reply
        except OSError:
            reply = Packet(get_reply_type(packet), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
            reply.payload = bytes('Failed to rename object', 'utf-8')

            print('Failed to rename object', server_path, 'to', new_path)

    def command_move(self, packet, p_data, server_path):
        new_path = self.__validate_path(p_data['new_path'])

        if new_path is None:
            reply = Packet(get_reply_type(packet), MSG_BAD_REQUEST, packet.id, packet.token)
            reply.payload = bytes('No new path was provided, or path is invalid', 'utf-8')

            print('No new path was provided, or path is invalid')
            return reply

        if not os.path.exists(server_path):
            reply = Packet(get_reply_type(packet), MSG_NOT_FOUND, packet.id, packet.token)
            reply.payload = bytes('The given source path does not exist', 'utf-8')

            print('Source path does not exist')
            return reply

        if os.path.exists(new_path):
            reply = Packet(get_reply_type(packet), MSG_FORBIDDEN, packet.id, packet.token)
            reply.payload = bytes('An object already exists at the destination path', 'utf-8')

            print('An object already exists at the destination path')
            return reply

        try:
            os.replace(server_path, new_path)
            data = {'client_cmd': 'move', 'status': 'moved'}

            reply = Packet(get_reply_type(packet), MSG_CHANGED, packet.id, packet.token)
            reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')

            print('Moved object', server_path, 'to', new_path)
            return reply
        except OSError:
            reply = Packet(get_reply_type(packet), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
            reply.payload = bytes('Failed to move object', 'utf-8')

            print('Failed to move object', server_path, 'to', new_path)

    def command_details(self, packet, p_data, server_path):
        if not os.path.exists(server_path):
            reply = Packet(get_reply_type(packet), MSG_NOT_FOUND, packet.id, packet.token)
            reply.payload = bytes('Path was not found', 'utf-8')

            print('Path was not found')
            return reply

        try:
            data = {'client_cmd': 'details', 'path': p_data['path']}

            stats = os.stat(server_path)

            if stat.S_ISDIR(stats.st_mode):
                data['type'] = 'folder'
                data['dir_contents'] = os.listdir(server_path)
                for dirs in data['dir_contents']:
                    dirs_path = os.stat(server_path + '/' + dirs)
                    if stat.S_ISDIR(dirs_path.st_mode):
                        data['dir_contents'] += os.listdir(server_path)

            elif stat.S_ISREG(stats.st_mode):
                data['type'] = 'file'
                data['size'] = stats.st_size
            else:
                data['type'] = 'unknown'

            reply = Packet(get_reply_type(packet), MSG_CHANGED, packet.id, packet.token)
            reply.payload = bytes(self.__jsonencoder.encode(data), 'utf-8')

            print('Sent data about object', server_path)
            return reply
        except OSError:
            reply = Packet(get_reply_type(packet), MSG_INTERNAL_SERVER_ERROR, packet.id, packet.token)
            reply.payload = bytes('Failed to retrieve data', 'utf-8')

            print('Failed to send data about object', server_path)

    def command_search(self, packet, data, server_path):
        reply = make_not_implemented(packet.id, packet.token)
        reply.payload = bytes('Server does not support this command (yet)', 'utf-8')
        return reply
