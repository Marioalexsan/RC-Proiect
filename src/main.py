from tkinter import *
from tkinter import ttk
import socket
import multiprocessing
import coap


def main():
    print('Starting CoAP server.')


    root = Tk()
    frame = ttk.Frame(root, padding=10, width=800, height=600)

    frame.grid()
    ttk.Label(frame, text='Hello World!').grid(column=0, row=0)
    ttk.Button(frame, text='Quit', command=root.destroy).grid(column=1, row=0)

    # La moment e mai mult un server pur UDP!!!
    server = coap.COAPServer()
    server.start()

    frame.pack()
    root.mainloop()

    server.stop()

    print('Closing CoAP server.')
    return


def coap_listen(sock):
    # A datagram has at most 65527 bytes of data
    data, addr = sock.recvfrom(65536)

    print("Got datagram from {0}: {1}".format(addr, data))

    return


if __name__ == '__main__':
    main()
