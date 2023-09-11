from typing import Literal

from tkinter import ttk
import tkinter as tk
import tkinter.filedialog
import pandastable as pdt
import pandas as pd


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

    def __init__(self, master, controller, **kwargs):
        self.master = master
        self.controller = controller
        super().__init__(master, **kwargs)
        self.title = tk.Label(self, text='Indisponibilidade [h/Ano]', justify='left')
        self.title.pack(padx=5,fill='x', expand=True, anchor='w')
        
        self.calculate = tk.Button(self, text = 'Calcular', state='disabled')
        self.calculate.bind('<ButtonRelease-1>', self.select)
        self.calculate.pack(padx=5, fill='x', expand=True, anchor='w')
        
        self.pack(anchor='nw')
        ttk.Separator(master).pack(pady=5, fill='x', anchor='n')
    
    def select(self, *args):
        self.controller.calculate_unavailabilty(scope= 'All')
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
    def __init__(self, master, controller, **kwargs):
        self.master = master
        self.controller = controller
        super().__init__(master,  **kwargs)
        tk.Label(self, text='Calcular DEC:').pack(anchor='nw')
        self.creaete_funcsel_btns()
        self.search_box()
        self.pack(anchor='nw')
        ttk.Separator(master).pack(pady=5, fill='x', anchor='n')

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

class ParmeterInputFrame(tk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.sel_failure()
        self.populate(1)

    def sel_failure(self):
        root = tk.Frame(self)

        label = tk.Label(root, text='Selecione a Falha:')
        label.grid(row=0, column=0)

        self.vars = tk.StringVar()
        self.cbox = ttk.Combobox(
            root,
            state='disabled',
            textvariable=self.vars,
            values=None)
        self.cbox.grid(row=0, column=1)
        
        root.pack()


    def populate(self, order: Literal['1', '2']):
        if order == '1':
            pass
        elif order == '2':
            pass

    def forget(self) -> None:
        for widget in self.winfo_children():
            widget.grid_forget()

class OutputNotebook:
    def __init__(self, master, **kwargs):
        self.notebook = CustomNotebook(master)
        self.add_table('Tabela 1')
        self.add_table('Tabela 2')

    def add_table(self, title,df: None | pd.DataFrame = None):
        ntab = tk.Frame(self.notebook)
        self.notebook.add(ntab, text=title)
        tableWindow = tk.Frame(ntab)
        inputsw = ParmeterInputFrame(ntab)
        if df is None:
            rows = 100
            cols = 26
            empty_data = [["" for _ in range(cols)] for _ in range(rows)]
            self.table = pdt.Table(
                tableWindow,
                rows=rows,
                cols=cols,
                data=empty_data, 
                showtoolbar=False, 
                showstatusbar=False)
            self.table.show()
        elif df.empty:
            return
        else:
            flatDf = df.reset_index()
            model = pdt.TableModel(flatDf)
            self.table = pdt.Table(tableWindow, model=model, showtoolbar=True, showstatusbar=True)
            self.table.show()
        tableWindow.pack(anchor='n', fill='both', expand=True)
        ttk.Separator(ntab).pack(pady=5, fill='x', anchor='n')
        inputsw.pack(anchor='s', fill='both', expand=True)
        self.notebook.pack(pady=(8,0), anchor='ne', fill='both', expand=True)

class View:

    def __init__(self, master : tk.Tk, controller):
        self.master = master
        # self.master.config(background='black')
        self.controller = controller
        self.create_menu() 
        self.status_bar = StatusBar(self.master, bg='white')
        ###
        self.options = tk.LabelFrame(self.master, text = 'Opções:')
        self.options.pack(side='left', fill='y', anchor='w')

        self.ind = IND(self.options, self.controller)
        self.dec = DEC(self.options, self.controller)
        ###

        self.output = OutputNotebook(self.master)

        self.status_bar.set('Importe uma rede!')
        

    # Menu itens -----------------
    def create_menu(self):
        menubar = tk.Menu(self.master, tearoff=False)
        self.master.config(menu = menubar)

        menubar.add_cascade(
            label='Arquivo',
            menu=self.create_file_menu(menubar),
        )

        menubar.add_command(
            label= 'Importar',
            command= self.controller.import_file,
        )
        # self.master.bind_all('<Control-i>', self.controller.import_file)

    def create_file_menu(self, menubar : tk.Menu):
        file_menu = tk.Menu(menubar, tearoff=False)
        
        file_menu.add_command(label='Novo')
        file_menu.add_command(label='Abrir')
        file_menu.add_command(label='Salvar')
        file_menu.add_command(
            label='Fechar',
            command=self.master.destroy,
        )
        file_menu.add_separator()
        file_menu.add_command(label='Opções')
        return file_menu

    def askfilewindow(self):
        return tkinter.filedialog.askopenfilename(
            defaultextension= ".PWF", 
            filetypes=[('All files', '*'), ('Arquivo Texto do Anarede', '.PWF')]
        )
