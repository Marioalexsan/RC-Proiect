from tkinter import *
from tkinter import ttk
from coap_server import *
from coap_parser import Parser
from src.pygubuapp import PygubuApp


# Overrides auto-generated UI from Pygubu
class Application(PygubuApp):
    # Functie de initializare a GUI / constructor
    def __init__(self):
        super().__init__()

        # Extra App setup

        self.initialize_frame = {}

        # Setup server

        self.parser = Parser()
        self.server = Server()

        self.server.packet_receivers[MSG_GET] = self.parser.onget
        self.server.packet_receivers[MSG_POST] = self.parser.onpost
        self.server.packet_receivers[MSG_PUT] = self.parser.onput
        self.server.packet_receivers[MSG_DELETE] = self.parser.ondelete
        self.server.packet_receivers[MSG_SEARCH] = self.parser.onsearch

        self.server.on_reply_sent = self.log_reply
        self.server.on_request_received = self.log_request
        self.__launch_time = time.time()

    def run(self):
        self.server.start()
        super().run()

    # Static UI Callbacks

    def on_quit_button(self):
        self.on_quitapp()
        self.mainwindow.destroy()

    def on_quitapp(self, event=None):
        self.server.stop()

    # Other

    def log_reply(self, packet: Packet):
        log = self.get_widget('server_log')

        text = 'Sent reply {0} - {1} to {2}\n'.format(type_str(packet.type), code_str(packet.code), packet.addr)
        log['text'] += '[{0:.2f}]'.format(time.time() - self.__launch_time) + text
        self.__trim_log()
        return

    def log_request(self, packet: Packet):
        log = self.get_widget('server_log')

        text = 'Request {0} - {1} from {2}\n'.format(type_str(packet.type), code_str(packet.code), packet.addr)
        log['text'] += '[{0:.2f}]'.format(time.time() - self.__launch_time) + text

        self.__trim_log()
        return

    def __trim_log(self):
        log = self.get_widget('server_log')

        log_text = log['text']
        while len(log_text) > 800:
            try:
                index = log_text.index('\n')
            except Exception:
                break
            log_text = log_text[(index + 1):]
        log['text'] = log_text
        return

    # UI Utils (thanks BDHomework)

    def swap_frame(self, name):
        if name in self.initialize_frame and callable(self.initialize_frame[name]):
            self.initialize_frame[name]()

        for k, v in self.mainwindow.children.items():
            v.pack_forget()

        target = self.builder.get_object(name)

        if target not in self.mainwindow.winfo_children():
            print('Warning: Swapping to a frame that isn\'t a scene!')

        target.pack()

    def get_widget(self, name):
        return self.builder.get_object(name)
