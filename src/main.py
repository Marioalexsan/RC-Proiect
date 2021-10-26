from tkinter import *
from tkinter import ttk
import socket
import multiprocessing
import coap

def main():
    server = coap.COAPServer()

    root = Tk()
    root.title("CoAP Server")
    frame = ttk.Frame(root, padding=50, width=800, height=600)

    frame.grid()
    ttk.Label(frame, text='Hello World!').grid(column=0, row=0)
    log = ttk.Labelframe(frame, text='', width=250, height=150, padding=30)
    log.grid(column=0, row=1, rowspan=2)

    ttk.Button(frame, text='Start', command=server.start).grid(column=1, row=0)
    ttk.Button(frame, text='Stop', command=server.stop).grid(column=1, row=1)
    ttk.Button(frame, text='Get message', command=lambda: logstuff(log, server)).grid(column=1, row=2)
    ttk.Button(frame, text='Quit', command=root.destroy).grid(column=1, row=3)

    for child in frame.winfo_children():
        child.grid_configure(padx=5, pady=5)

    # La moment e mai mult un server pur UDP!!!

    frame.pack()
    root.mainloop()

    server.stop()

    print('Closing application.')
    return

def logstuff(log, server: coap.COAPServer):
    msg = server.getdata()

    if msg is None:
        log['text'] = "Nothin', lol"
    else:
        log['text'] = ""

    while msg is not None:
        log['text'] = log['text'] + '\n' + msg[0].decode("utf-8")
        msg = server.getdata()


if __name__ == '__main__':
    main()
