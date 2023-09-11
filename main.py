import tkinter as tk


from model import Model
from view import View
from controller import Controller

class App(tk.Tk):
    
    def __init__(self):
        super().__init__()

        self.state('iconic')
        self.title("DEC-AT")    

        # Creating a Model
        model = Model()
        controller = Controller(model)
        view = View(self, controller)
        model.set_observer(view)
        controller.set_view(view)


if __name__ == "__main__":
    app = App()
    app.mainloop()