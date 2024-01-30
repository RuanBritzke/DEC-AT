import tkinter as tk
import warnings

from view import View
from controller import Controller
from utils import functions

warnings.simplefilter(action="ignore", category=FutureWarning)


# The class `App` is a subclass of `tk.Tk` and represents an application window with a specific title,
# size, and icon.
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconbitmap(functions.resource_path("imgs\\CELESC.ico"))
        self.minsize(600, 600)
        self.state("zoomed")
        self.title("DEC-AT")

        view = View(self)
        Controller(view)


if __name__ == "__main__":
    app = App()
    app.mainloop()
