from tkinter import *
from tkinter import ttk


def main():
    print('Starting application!')

    root = Tk()
    frame = ttk.Frame(root, padding=10, width=800, height=600)

    frame.grid()
    ttk.Label(frame, text='Hello World!').grid(column=0, row=0)
    ttk.Button(frame, text='Quit', command=root.destroy).grid(column=1, row=0)

    frame.pack()
    root.mainloop()

    print('Quitting application!')
    return


if __name__ == '__main__':
    main()
