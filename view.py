import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
from tkinter import messagebox
import pandas as pd
import pandastable as pdt

from typing import Literal


pd.options.mode.chained_assignment = None  # default='warn'

class Message(tk.Toplevel):
    
    def __init__(self, message):
        super(Message, self).__init__()
        self.title('Carregando')
        tk.Message(self, text= message, padx=20, pady=20).pack()

    def close(self):
        self.destroy()



class StatusBar(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(highlightbackground='black', highlightthickness=1)
        self.label = tk.Label(self, text= '', bg = 'white')
        self.label.pack(side='left')
        self.pack(side='bottom', fill='x')

    def set(self, newText):
        self.label.config(text=newText)

    def clear(self):
        self.label.config(text='')

class IND(tk.Frame):

    def __init__(self, root, master, controller, **kwargs):
        self.root = root
        self.master = master
        self.controller = controller
        super().__init__(master, **kwargs)
        self.title = tk.Label(self, text='Indisponibilidade [h/Ano]', justify='left')
        self.title.pack(padx=5,fill='x', expand=True, anchor='w')
        
        self.calculate = tk.Button(self, text = 'Calcular', state='disabled')
        self.calculate.bind('<ButtonRelease-1>', self.startSearch)
        self.calculate.pack(padx=5, fill='x', expand=True, anchor='w')
        
        self.pack(anchor='nw')
        ttk.Separator(master).pack(pady=5, fill='x', anchor='n')
    
    def startSearch(self, *args):
        self.root.status_bar.set('Calculando Indisponibilidade para todas as SEs')
        self.controller.computeUnavailabilty()
        self.root.status_bar.set('Pronto!')
        return

    def enable(self, _state='normal'):
        def set_state(widget:tk.Widget):
            for ch in widget.winfo_children():
                set_state(ch)
            if 'state' in  widget.keys():
                widget.config(state = _state)
        set_state(self)

    def disable(self):
        self.enable('disable')

class DEC(tk.Frame):
    def __init__(self, root, master, controller, **kwargs):
        self.root = root
        self.master = master
        self.controller = controller
        super().__init__(master,  **kwargs)
        tk.Label(self, text='Calcular DEC:').pack(anchor='nw')
        self.creaete_funcsel_btns()
        self.search_box()
        self.pack(anchor='nw')
        ttk.Separator(master).pack(pady=5, fill='x', anchor='n')

    def startSearch(self, *args):
        self.root.status_bar.set(f'Calculando Indisponibilidade para {self.cbox.get()}')
        self.controller.computeUnavailabilty(entry = self.cbox.get())
        self.root.status_bar.set('Pronto!')
        
    def search_box(self):
        root = tk.Frame(self)
        self.vars = tk.StringVar()
        self.cbox = ttk.Combobox(
            root,
            state='disabled',
            textvariable=self.vars,
            values=None, 
            postcommand= self.updtcblist)
        self.cbox.grid(row=0, column=0, padx=5, pady=5)
        self.search = tk.Button(
            root, 
            text="Procurar", 
            state='disabled')
        self.search.grid(row=0, column=1, padx=5, pady=5)
        root.pack(fill='x', expand=True)
        self.search.bind('<ButtonRelease-1>', self.startSearch)


    def creaete_funcsel_btns(self):
        labels = ["Por SE", "Por BARRA"]
        options = list(range(len(labels)))
        self.var = tk.StringVar()
        self.var.set(None)
        for i, (label, option) in enumerate(zip(labels, options)):
            radio_btn = tk.Radiobutton(
                self,
                text=label,
                state= 'disabled',
                variable= self.var,
                value= option,
                command= lambda:self.controller.set_buses_or_subs(self.var.get()))
            radio_btn.pack(anchor='nw')

    def enable(self, _state='normal'):
        def set_state(widget:tk.Widget):
            for ch in widget.winfo_children():
                set_state(ch)
            if 'state' in  widget.keys():
                widget.config(state = _state)
        set_state(self)

    def disable(self):
        self.enable('disable')

    def updtcblist(self):
        values = self.controller.buses_or_subs
        self.cbox['values'] = values

class ParameterInputFrame(tk.Frame):

    def __init__(self, master, dataframe, pandastable, **kwargs):
        super().__init__(master, **kwargs)
        self.dataframe = dataframe
        self.pandastable = pandastable

    def forget(self) -> None:
        for widget in self.winfo_children():
            widget.grid_forget()

class OutputNotebook:
    def __init__(self, master : 'View', controller, **kwargs):
        self.master = master
        self.controller = controller
        self.notebook = CustomNotebook(master)
        self.notebook.pack(pady=(8,0), anchor='ne', fill='both', expand=True)
        self.add_table('Exemplo')

    def add_table(self, title, df: pd.DataFrame | None = None):
        ntab = tk.Frame(self.notebook)
        tableWindow = tk.Frame(ntab)
        
        if df is None:
            ntabLabel = tk.Label(ntab, text="Seus outputs serão gerados aqui!", justify='left')
            ntabLabel.pack(anchor='n', fill='x', expand=True)
        elif df.empty:
            return
        else:
            df_visualization = df.copy()
            model = pdt.TableModel(df_visualization)
            self.table = pdt.Table(tableWindow, model=model, showtoolbar=True, showstatusbar=True)
            self.table.show()
            tableWindow.pack(anchor='n', fill='both', expand=True)
            ttk.Separator(ntab).pack(pady=5, fill='x', anchor='n')
            inputsw = ParameterInputFrame(ntab, df, self.table)
            inputsw.pack(anchor='s', fill='both', expand=True)
        self.notebook.add(ntab, text=title)
        self.notebook.select(ntab)
        return

class View:

    def __init__(self, master : tk.Tk):
        self.master = master
        self.status_bar = StatusBar(self.master, bg='white')
        self.options = tk.LabelFrame(self.master, text = 'Opções:')
        self.options.pack(side='left', fill='y', anchor='w')
        self.status_bar.set('Importe uma rede!')

    def set_controller(self, controller):
        self.controller = controller
        self.my__post__init__()

    def my__post__init__(self):
        self.create_menu() 
        self.ind = IND(self, self.options, self.controller)
        self.dec = DEC(self, self.options, self.controller)
        self.output = OutputNotebook(self.master, self.controller)

    def create_menu(self):
        menubar = tk.Menu(self.master, tearoff=False)
        self.master.config(menu = menubar)
        menubar.add_command(
            label= 'Importar',
            command= self.controller.import_file,
        )

    def askfilewindow(self):
        return tkinter.filedialog.askopenfilename(
            defaultextension= ".PWF", 
            filetypes=[('All files', '*'), ('Arquivo Texto do Anarede', '.PWF')]
        )

class CustomNotebook(ttk.Notebook):
    """A ttk Notebook with close buttons on each tab"""

    __initialized = False

    def __init__(self, *args, **kwargs):
        if not self.__initialized:
            self.__initialize_custom_style()
            self.__inititialized = True

        kwargs["style"] = "CustomNotebook"
        ttk.Notebook.__init__(self, *args, **kwargs)

        self._active = None

        self.bind("<ButtonPress-1>", self.on_close_press, True)
        self.bind("<ButtonRelease-1>", self.on_close_release)

    def on_close_press(self, event):
        """Called when the button is pressed over the close button"""

        element = self.identify(event.x, event.y)

        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            self.state(['pressed'])
            self._active = index
            return "break"

    def on_close_release(self, event):
        """Called when the button is released"""
        if not self.instate(['pressed']):
            return

        element =  self.identify(event.x, event.y)
        if "close" not in element:
            # user moved the mouse off of the close button
            return

        index = self.index("@%d,%d" % (event.x, event.y))

        if self._active == index:
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>")

        self.state(["!pressed"])
        self._active = None

    def __initialize_custom_style(self):
        style = ttk.Style()
        self.images = (
            tk.PhotoImage("img_close", data='''
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                '''),
            tk.PhotoImage("img_closeactive", data='''
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs=
                '''),
            tk.PhotoImage("img_closepressed", data='''
                R0lGODlhCAAIAMIEAAAAAOUqKv9mZtnZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
            ''')
        )

        style.element_create("close", "image", "img_close",
                            ("active", "pressed", "!disabled", "img_closepressed"),
                            ("active", "!disabled", "img_closeactive"), border=8, sticky='')
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("CustomNotebook.padding", {
                        "side": "top",
                        "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.focus", {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.label", {"side": "left", "sticky": ''}),
                                    ("CustomNotebook.close", {"side": "left", "sticky": ''}),
                                ]
                        })
                    ]
                })
            ]
        })
    ])