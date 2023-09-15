"""Ao futuro Engenheiro/Estagiario que for manter/refatorar este programa: Minhas sinceras desculpas """

import tkinter as tk
import warnings

from model import Model
from view import View
from controller import Controller

warnings.simplefilter(action='ignore', category=FutureWarning)

class App(tk.Tk):
    
    def __init__(self):
        super().__init__()

        self.geometry("500x350")
        self.state('iconic')
        self.title("DEC-AT")    

        model = Model()
        view = View(self)
        Controller(model, view)
        model.set_observer(view)


if __name__ == "__main__":
    app = App()
    app.mainloop()