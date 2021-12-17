# coap.py
# Defines many constants and other goodies related to CoAP

# FIXME: Do we limit ourselves to RFC-7252, or do we also use the updated specifications (such as RFC-8132)? -mario

# Misc Constants
COAP_VERSION = 1

# Message types
TYPE_CON = 0
TYPE_NON = 1
TYPE_ACK = 2
TYPE_RESET = 3

# Message classes
CLASS_METHOD = 0
CLASS_SUCCESS = 2
CLASS_CLIENT_ERROR = 4
CLASS_SERVER_ERROR = 5
CLASS_SIGNAL_CODE = 7  # RFC-8323

# Non-Standard Message Codes
MSG_SEARCH = (0, 8)

# Empty Message Code
MSG_EMPTY = (0, 0)

# Method Codes
MSG_GET = (0, 1)
MSG_POST = (0, 2)
MSG_PUT = (0, 3)
MSG_DELETE = (0, 4)

# Success Codes
MSG_CREATED = (2, 1)
MSG_DELETED = (2, 2)
MSG_VALID = (2, 3)
MSG_CHANGED = (2, 4)
MSG_CONTENT = (2, 5)

# Client Error Codes
MSG_BAD_REQUEST = (4, 0)
MSG_UNAUTHORIZED = (4, 1)
MSG_BAD_OPTION = (4, 2)
MSG_FORBIDDEN = (4, 3)
MSG_NOT_FOUND = (4, 4)
MSG_METHOD_NOT_ALLOWED = (4, 5)
MSG_NOT_ACCEPTABLE = (4, 6)
MSG_REQUEST_ENTITY_INCOMPLETE = (4, 8)
MSG_CONFLICT = (4, 9)
MSG_PRECONDITION_FAILED = (4, 12)
MSG_REQUEST_ENTITY_TOO_LARGE = (4, 13)
MSG_UNSUPPORTED_CONTENT_FORMAT = (4, 15)

# Server Error Codes
MSG_INTERNAL_SERVER_ERROR = (5, 0)
MSG_NOT_IMPLEMENTED = (5, 1)
MSG_BAD_GATEWAY = (5, 2)
MSG_SERVICE_UNAVAILABLE = (5, 3)
MSG_GATEWAY_TIMEOUT = (5, 4)
MSG_PROXYING_NOT_SUPPORTED = (5, 5)

# Signalling Codes - RFC-8323
MSG_UNASSIGNED = (7, 0)
MSG_CSM = (7, 1)
MSG_PING = (7, 2)
MSG_PONG = (7, 3)
MSG_RELEASE = (7, 4)
MSG_ABORT = (7, 5)

# Option IDs
OPT_IF_MATCH = 1
OPT_URI_HOST = 3
OPT_ETAG = 4
OPT_IF_NONE_MATCH = 5
OPT_URI_PORT = 7
OPT_LOCATION_PATH = 8
OPT_URI_PATH = 11
OPT_CONTENT_FORMAT = 12
OPT_MAX_AGE = 14
OPT_URI_QUERY = 15
OPT_ACCEPT = 17
OPT_LOCATION_QUERY = 20
OPT_PROXY_URI = 35
OPT_PROXY_SCHEME = 39
OPT_SIZE1 = 60

# List of Critical Options
# Critical Options that fail to parse must raise an error
OPTIONS_CRITICAL = [1, 3, 5, 7, 11, 15, 17, 35, 39]

# List of Repeatable Options
# Options that are repeatable can appear more than once
OPTIONS_REPEATABLE = [1, 4, 8, 11, 15, 20]

# Media types
MEDIA_TEXT = 0
MEDIA_LINK_FORMAT = 40
MEDIA_XML = 41
MEDIA_OCTET_STREAM = 42
MEDIA_EXI = 47
MEDIA_JSON = 50

# Communication parameters
COMM_ACK_TIMEOUT = 2
COMM_ACK_RANDOM_FACTOR = 1.5
COMM_MAX_RETRANSMIT = 4
COMM_NSTART = 1
COMM_DEFAULT_LEISURE = 5
COMM_PROBING_RATE = 1

COMM_MAX_TRANSMIT_SPAN = 45
COMM_MAX_TRANSMIT_WAIT = 93
COMM_MAX_LATENCY = 100
COMM_PROCESSING_DELAY = 2
COMM_MAX_RTT = 202
COMM_EXCHANGE_LIFETIME = 247
COMM_NON_LIFETIME = 145


# defineste exceptiile aparute in urma procesarii pachetelor Co-AP
class ParseException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


# Clasa pentru definirea unui pachet Co-AP cu toate campurile sale
class Packet:
    # Constructor
    def __init__(self, m_type=TYPE_NON, m_code=MSG_EMPTY, m_id=0, m_token=bytes(0)):

        # Members
        self.version = COAP_VERSION
        self.type = m_type
        self.code = m_code
        self.id = m_id
        self.options = {}
        self.payload = bytes(0)
        self.token = m_token

        # Send / receive address
        self.addr = ('127.0.0.1', 5683)
        return

    # Initializeaza un pachet coap dintr-un sir de octeti
    # Parsarea este facuta dupa RFC7252
    def parse(self, data):
        if data is None:
            raise ParseException("No data provided")

        bytecount = len(data)
        bytesdone = 0

        # primii 4 biti sunt obligatorii in orice pachet CoAP
        if bytecount < 4:
            raise ParseException("Not a CoAP packet")

        # Header Base

        self.version = (0xC0 & data[0]) >> 6
        self.type = (0x30 & data[0]) >> 4
        self.code = ((data[1] >> 5) & 0x07, data[1] & 0x1F)
        self.id = (data[2] << 8) | data[3]

        token_length = 0x0F & data[0]

        bytesdone += 4

        # Tokens

        if bytecount < bytesdone + token_length:
            raise ParseException("Bad packet")

        self.token = bytes(data[4:(4 + token_length)])

        bytesdone += token_length

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
        # restul mesajului reprezinta date, adaugam la packet

        self.payload = data[bytesdone:bytecount]

        return

    # Functie de convertire a unui pachet coap la un sir de octeti / operatiunea inversa parsarii
    def tobytes(self):
        # Write base header

        token_length = len(self.token)

        if token_length > 8:
            raise ParseException("Token must be between 0 and 8 bytes (got {0})".format(token_length))

        data = [
            ((0x3 & self.version) << 6) | ((0x3 & self.type) << 4) | (0xF & token_length),
            ((self.code[0] & 0x7) << 5) | (self.code[1] & 0x1F), (self.id & 0xFF00) >> 8,
            self.id & 0x00FF
        ]

        # Write token (if any)

        for i in range(0, token_length):
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
        text = ""
        text += "Version: {0}, ".format(self.version)
        text += "Type: {0}, ".format(self.type)
        text += "Class: {0}, ".format(self.code[0])
        text += "Code: {0}, ".format(self.code[1])
        text += "Message ID: {0}\n".format(self.id)
        text += "Option count: {0}\n".format(len(self.options))

        for pair in self.options.items():
            for option in pair[1]:
                text += "{0} = {1}; ".format(pair[0], option.decode("utf-8"))

        text += '\n'
        text += 'Payload: [{0}]'.format(self.payload.decode("utf-8"))

        return text

    def get_reply_type(self):
        if self.type == TYPE_CON:
            return TYPE_ACK
        elif self.type == TYPE_NON:
            return TYPE_NON
        else:
            return TYPE_ACK


# Creates a reset reply with the given message ID
def make_reset(msg_id, msg_token):
    reply = Packet(TYPE_RESET, MSG_EMPTY, msg_id, msg_token)
    return reply


# Creates an empty ACK message with the given message ID
# This can be used to separate response from request acknowledgement
def make_empty_ack(msg_id, msg_token):
    reply = Packet(TYPE_ACK, MSG_EMPTY, msg_id, msg_token)
    return reply


def make_not_implemented(msg_id, msg_token):
    reply = Packet(TYPE_ACK, MSG_NOT_IMPLEMENTED, msg_id, msg_token)
    return reply


def get_reply_type(packet: Packet):
    if packet.type == TYPE_CON:
        return TYPE_ACK
    elif packet.type == TYPE_NON:
        return TYPE_NON
    else:
        return TYPE_ACK


def type_str(value):
    strmap = {
        TYPE_CON: 'CON',
        TYPE_NON: 'NON',
        TYPE_ACK: 'ACK',
        TYPE_RESET: 'RESET'
    }

    return strmap[value]


def code_str(value):
    strmap = {
        MSG_EMPTY: 'EMPTY',

        MSG_GET: 'GET',
        MSG_POST: 'POST',
        MSG_PUT: 'PUT',
        MSG_DELETE: 'DELETE',
        MSG_SEARCH: 'SEARCH',

        MSG_CREATED: 'CREATED',
        MSG_DELETED: 'DELETED',
        MSG_VALID: 'VALID',
        MSG_CHANGED: 'CHANGED',
        MSG_CONTENT: 'CONTENT',

        MSG_BAD_REQUEST: 'BAD REQUEST',
        MSG_UNAUTHORIZED: 'UNAUTHORIZED',
        MSG_BAD_OPTION: 'BAD OPTION',
        MSG_FORBIDDEN: 'FORBIDDEN',
        MSG_NOT_FOUND: 'NOT FOUND',
        MSG_METHOD_NOT_ALLOWED: 'METHOD NOT ALLOWED',
        MSG_NOT_ACCEPTABLE: 'NOT ACCEPTABLE',
        MSG_REQUEST_ENTITY_INCOMPLETE: 'RE INCOMPLETE',
        MSG_CONFLICT: 'CONFLICT',
        MSG_PRECONDITION_FAILED: 'PRECONDITION FAILED',
        MSG_REQUEST_ENTITY_TOO_LARGE: 'RE TOO LARGE',
        MSG_UNSUPPORTED_CONTENT_FORMAT: 'UNSUPPORTED CONTENT FORMAT',

        MSG_INTERNAL_SERVER_ERROR: 'INTERNAL SERVER ERROR',
        MSG_NOT_IMPLEMENTED: 'NOT IMPLEMENTED',
        MSG_BAD_GATEWAY: 'BAD GATEWAY',
        MSG_SERVICE_UNAVAILABLE: 'SERVICE UNAVAILABLE',
        MSG_GATEWAY_TIMEOUT: 'GATEWAY TIMEOUT',
        MSG_PROXYING_NOT_SUPPORTED: 'PROXYING NOT SUPPORTED',
    }

    return strmap[value]

