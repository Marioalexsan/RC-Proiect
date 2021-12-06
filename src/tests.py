import random
import socket
import sys
from coap import *
import json


SOCKET_ADDR = ('', 1337)
TARGET_ADDR = ('127.0.0.1', 5683)
REPLY_TIMEOUT = 10

json_encoder = json.JSONEncoder()
json_decoder = json.JSONEncoder()


def randomize_id():
    return int(random.random() * 19573826589) % 65535


def randomize_token():
    length = int(random.random() * 4235226637) % 6
    token = []
    for i in range(3, 3 + length):
        token.append(int(random.random() * 43525) % 255)
    return bytes(token)


def showhelp():
    name = 'tests.py'
    print('=== CoAP Server testing application ===')
    print('> Usage:')
    print('> \'python3 {0} create <path> [folder/file]\' to create a folder or file.'.format(name))
    print('> \'python3 {0} delete <path>\' to delete an object.'.format(name))
    exit(0)


def wait_for_reply(sock):
    try:
        print('Waiting for reply; timeout =', REPLY_TIMEOUT, 'seconds')
        sock.settimeout(REPLY_TIMEOUT)
        data, addr = sock.recvfrom(65527)
        packet = Packet()
        packet.addr = addr
        packet.parse(data)
        print('Received message from', packet.addr)
        print('ID', packet.id)
        print('Type', packet.type)
        print('Code', packet.code)
        print('Token: ', packet.token)
        print('Payload: ', packet.payload)
    except socket.timeout:
        print('Request timed out!')
    except TimeoutError:
        print('Request timed out!')
    except ParseException as e:
        print('Packet caused a CoAP exception! Error message: ', e)


def create(sock, path, objtype):
    if objtype not in ['folder', 'file']:
        pass

    payload = {'cmd': 'create', 'path': path, 'type': objtype}

    request = Packet(TYPE_NON, MSG_POST, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    wait_for_reply(sock)
    pass


def delete(sock, path):
    payload = {'cmd': 'delete', 'path': path}

    request = Packet(TYPE_NON, MSG_POST, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    # Send message

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    # Wait for a reply
    wait_for_reply(sock)
    pass


def openfile(sock, path):
    payload = {'cmd': 'open', 'path': path}

    request = Packet(TYPE_NON, MSG_GET, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    # Send message

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    # Wait for a reply

    wait_for_reply(sock)
    pass


def savefile(sock, path, content):
    payload = {'cmd': 'save', 'path': path, 'content': content}

    request = Packet(TYPE_NON, MSG_POST, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    # Send message

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    wait_for_reply(sock)
    pass


def rename(sock, path, name):
    payload = {'cmd': 'rename', 'path': path, 'name': name}

    request = Packet(TYPE_NON, MSG_POST, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    # Send message

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    wait_for_reply(sock)
    pass


def move(sock, path, new_path):
    payload = {'cmd': 'move', 'path': path, 'new_path': new_path}

    request = Packet(TYPE_NON, MSG_POST, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    # Send message

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    wait_for_reply(sock)
    pass


def details(sock, path):
    payload = {'cmd': 'details', 'path': path}

    request = Packet(TYPE_NON, MSG_GET, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    # Send message

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    wait_for_reply(sock)
    pass

def searchcommand(sock, path, target_name_regex):
    payload = {'cmd': 'search', 'path': path, 'target_name_regex': target_name_regex}

    request = Packet(TYPE_NON, MSG_SEARCH, randomize_id(), randomize_token())
    request.payload = bytes(json_encoder.encode(payload), 'utf-8')

    print('Using token', request.token, 'and ID', request.id)

    # Send message

    sock.sendto(request.tobytes(), TARGET_ADDR)
    print('Sent request')

    wait_for_reply(sock)
    pass

def main():
    argc = len(sys.argv)

    if argc == 1:
        showhelp()

    cmd = sys.argv[1]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SOCKET_ADDR)

    if cmd == 'create' and argc == 4:
        create(sock, sys.argv[2], sys.argv[3])
    elif cmd == 'delete' and argc == 3:
        delete(sock, sys.argv[2])
    elif cmd == 'open' and argc == 3:
        openfile(sock, sys.argv[2])
    elif cmd == 'save' and argc >= 3:
        savefile(sock, sys.argv[2], ' '.join(sys.argv[3:]))
    elif cmd == 'rename' and argc == 4:
        rename(sock, sys.argv[2], sys.argv[3])
    elif cmd == 'move' and argc == 4:
        move(sock, sys.argv[2], sys.argv[3])
    elif cmd == 'details' and argc == 3:
        details(sock, sys.argv[2])
    elif cmd == 'search' and argc == 4:
        searchcommand(sock, sys.argv[2], sys.argv[3])
    else:
        print('Command was not understood!')
        showhelp()

    sock.close()


if __name__ == '__main__':
    main()
