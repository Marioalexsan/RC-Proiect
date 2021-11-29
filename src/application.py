from tkinter import *
from tkinter import ttk
from coap_server import *
from coap_parser import Parser


class Application(Tk):
    # Functie de initializare a GUI / constructor
    def __init__(self):
        super().__init__()

        self.parser = Parser()

        # Setup server
        self.server = Server()

        self.server.receivers[MSG_GET] = self.parser.onget
        self.server.receivers[MSG_POST] = self.parser.onpost
        self.server.receivers[MSG_PUT] = self.parser.onput
        self.server.receivers[MSG_DELETE] = self.parser.ondelete
        self.server.receivers[MSG_SEARCH] = self.parser.onsearch

        self.server.on_reply_sent = self.log_reply
        self.server.on_request_received = self.log_request
        self.__launch_time = time.time()

        # Setup GUI

        self.title("CoAP Server")

        self.geometry('800x600')
        self.wm_resizable(False, False)

        frame = ttk.Frame(self, padding=50)
        frame.bind('<Destroy>', lambda event: self.server.stop())
        frame.grid()

        self.log = ttk.Labelframe(frame, text='Messages will appear here...', width=320, height=480, padding=30)
        self.log.grid(column=0, row=0, rowspan=3)

        self.log_data = ttk.Label(self.log, text='')
        self.log_data.grid(column=0, row=0)

        self.status = ttk.Label(frame, text='Server is off')
        self.status.grid(column=1, row=0)
        self.start_stop = ttk.Button(frame, text='Start', command=self.__onstart)
        self.start_stop.grid(column=1, row=1)

        ttk.Button(frame, text='Quit', command=self.__onquit).grid(column=1, row=2)

        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

        frame.pack()
        self.__update_interface()

    def log_reply(self, packet: Packet):
        text = 'Sent reply {0} - {1} to {2}\n'.format(type_str(packet.type), code_str(packet.code), packet.addr)
        self.log_data['text'] += '[{0:.2f}]'.format(time.time() - self.__launch_time) + text
        self.__trim_log()
        return

    def log_request(self, packet: Packet):
        text = 'Request {0} - {1} from {2}\n'.format(type_str(packet.type), code_str(packet.code), packet.addr)
        self.log_data['text'] += '[{0:.2f}]'.format(time.time() - self.__launch_time) + text

        self.__trim_log()
        return

    def __trim_log(self):
        log_text = self.log_data['text']
        while len(log_text) > 800:
            try:
                index = log_text.index('\n')
            except Exception:
                break
            log_text = log_text[(index + 1):]
        self.log_data['text'] = log_text
        return

    def startapp(self):
        self.mainloop()

    def __onstart(self):
        self.server.start()
        self.__update_interface()

    def __onstop(self):
        self.server.stop()
        self.__update_interface()

    def __onquit(self):
        self.destroy()
        self.server.stop()

    def __update_interface(self):
        if self.server.is_active():
            self.status['text'] = 'Server is on'
            self.start_stop['command'] = self.__onstop
            self.start_stop['text'] = "Stop"
        else:
            self.status['text'] = 'Server is off'
            self.start_stop['command'] = self.__onstart
            self.start_stop['text'] = "Start"
