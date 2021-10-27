from tkinter import *
from tkinter import ttk
import coap


class Application(Tk):
    def __init__(self):
        super().__init__()

        self.server = coap.CoAPServer()
        self.server.onreceive = self.__onreceive
        self.title("CoAP Server")

        frame = ttk.Frame(self, padding=50, width=800, height=600)
        frame.grid()

        self.log = ttk.Labelframe(frame, text='Messages will appear here...', width=250, height=150, padding=30)
        self.log.grid(column=0, row=1, rowspan=2)

        self.status = ttk.Label(frame, text='Server is off')
        self.status.grid(column=1, row=0)
        ttk.Button(frame, text='Start', command=self.__onstart).grid(column=1, row=1)
        ttk.Button(frame, text='Stop', command=self.__onstop).grid(column=1, row=2)
        ttk.Button(frame, text='Quit', command=self.destroy).grid(column=1, row=3)

        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

        frame.pack()

    def startapp(self):
        self.mainloop()

    def __onstart(self):
        self.server.start()
        self.status['text'] = 'Server is on'

    def __onstop(self):
        self.server.stop()
        self.status['text'] = 'Server is off'

    def __onreceive(self, packet):
        if packet is None:
            self.log['text'] = "Null packet received!"
        else:
            self.log['text'] = "Received packet:\n" + str(packet)

    def __onquit(self):
        self.destroy()
        self.server.stop()
        self.status['text'] = 'Server is ded'
