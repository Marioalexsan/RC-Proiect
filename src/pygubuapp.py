import pathlib
import tkinter as tk
import tkinter.ttk as ttk
import pygubu

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "pygubu.ui"


class PygubuApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('mainwindow', master)
        builder.connect_callbacks(self)
    
    def run(self):
        self.mainwindow.mainloop()

    def on_quit_button(self):
        pass

    def on_quitapp(self, event=None):
        pass


if __name__ == '__main__':
    app = PygubuApp()
    app.run()

