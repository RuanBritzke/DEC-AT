from collections import defaultdict
import tkinter as tk
import tkinter.filedialog
import pandas as pd
from tkinter import ttk

from custompandastable import *
from literals import *

pd.options.mode.chained_assignment = None  # default='warn'


class StatusBar(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(highlightbackground="black", highlightthickness=1)
        self.label = tk.Label(self, text="", bg="white")
        self.label.pack(side="left")
        self.pack(side="bottom", fill="x")

    def set(self, newText):
        self.label.config(text=newText)

    def clear(self):
        self.label.config(text="")


class DEC(tk.Frame):
    cbox_values = None

    def __init__(self, root, master, controller, **kwargs):
        self.root = root
        self.master = master
        self.controller = controller
        super().__init__(master, **kwargs)
        tk.Label(self, text="Calcular DEC:").pack(anchor="nw")
        self.create_function_selection_buttons()
        self.search_box()
        self.pack(anchor="nw")
        ttk.Separator(master).pack(pady=5, fill="x", anchor="n")

    def startSearch(self, *args):
        self.root.status_bar.set(f"Calculando Indisponibilidade para {self.cbox.get()}")
        self.controller.computeUnavailabilty(entry=self.cbox.get())
        self.root.status_bar.set("Pronto!")

    def search_box(self):
        root = tk.Frame(self)
        self.vars = tk.StringVar()
        self.cbox = ttk.Combobox(
            root,
            state="disabled",
            textvariable=self.vars,
            postcommand=self.update_cblist,
        )
        self.cbox.grid(row=0, column=0, padx=5, pady=5)
        self.search = tk.Button(root, text="Procurar", state="disabled")
        self.search.grid(row=0, column=1, padx=5, pady=5)
        root.pack(fill="x", expand=True)
        self.search.bind("<ButtonRelease-1>", self.startSearch)

    def create_function_selection_buttons(self):
        labels = ["Todas SEs", "Por SE", "Por BARRA"]
        self.var = tk.IntVar()
        self.var.set(0)
        for i, label in enumerate(labels):
            radio_btn = tk.Radiobutton(
                self,
                text=label,
                state="disabled",
                variable=self.var,
                value=i,
                command=lambda: self.radio_button_selection(self.var.get()),
            )
            radio_btn.pack(anchor="nw")

    def radio_button_selection(self, option: int):
        if option == 0:
            self.cbox.config(state="disabled")
            self.cbox_values = "Todas SEs"
            self.cbox.set("Todas SEs")
        if option == 1:
            self.cbox.config(state="normal")
            self.cbox_values = self.controller.get_options_cbox_values(to="SUB")
            self.cbox.set(self.cbox_values[0])
        elif option == 2:
            self.cbox.config(state="normal")
            self.cbox_values = self.controller.get_options_cbox_values(to="BUS")
            self.cbox.set(self.cbox_values[0])

    def enable(self, _state="normal"):
        def set_state(widget: tk.Widget):
            for ch in widget.winfo_children():
                set_state(ch)
            if "state" in widget.keys():
                widget.config(state=_state)

        set_state(self)

    def disable(self):
        self.enable("disable")

    def update_cblist(self):
        self.cbox["values"] = self.cbox_values


class FailureTreatmentFrame(tk.Frame):

    failure_types_params = {DLINE : None,
                            XFMR : None}
    
    def __init__(self, master, controller, title, view_table: pd.DataFrame, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.title = title
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.view_table = view_table
        if view_table.columns[-3] == "FALHA 2":
            self.failures = self.view_table.apply(
                lambda row: f"{row['FALHA 1']} <-> {row['FALHA 2']}"
                if row["FALHA 2"] is not None
                else f"{row['FALHA 1']}",
                axis=1,
            ).tolist()
        else:
            self.failures = self.view_table["FALHA 1"].tolist()
        
        self.create_widgets()

    def create_widgets(self):
        self.create_failure_selection_frame()
        self.create_parameters_input_frame(order = None, failure_type = None)

    def create_failure_selection_frame(self):
        failure_selection_frame = tk.Frame(self)
        failure_selection_label = tk.Label(
            failure_selection_frame, text="Selecione a Falha:", justify="left"
        )

        self.failure_vars = tk.StringVar()

        self.failure_selection_cbox = ttk.Combobox(
            failure_selection_frame,
            values= self.failures,
            textvariable=self.failure_vars,
        )
        cmd = self.failure_selection_cbox.register(self.failure_selected)
        self.failure_selection_cbox.bind("<<ComboboxSelected>>", cmd) # Tem que ser assim pra funcionar, não sei por que.
        self.failure_selection_cbox.set('Falha')


        failure_selection_label.pack(anchor="nw", padx=5, pady=5, expand=True)
        self.failure_selection_cbox.pack(fill="x", padx=5, pady=5, expand=True)

        failure_selection_frame.pack(anchor='nw', fill='x')
 
    def create_parameters_input_frame(self, order: int, failure_type: str): # TODO: Change this to int value input widet
        parameters_input_frame = tk.Frame(self)
        if failure_type is None:
            return
        self.create_dline_params_frame(parameters_input_frame)
        parameters_input_frame.pack(anchor='center', fill='both', expand=True)

    def create_dline_params_frame(self, master):
        dline_params_frame = tk.Frame(master)
        dline_params_frame.pack(anchor='center', fill='both', expand=True)

        consumers_transferible_label = tk.Label(dline_params_frame, text="Percentual de consumidores transferiveis via alimentadores MT por chave manual [%]", justify='left')
        consumers_transferible_label.grid(row=0, sticky='NE')
        
        consumers_transferible_text = tk.Text(dline_params_frame)
        consumers_transferible_text.grid(row=1, sticky='NE')
        

        action_time_label = tk.Label(dline_params_frame, text="Tempo para acionamento da chave para transferir a carga entre alimentadores [h]", justify='left')
        action_time_label.grid(row=2)
        
        action_time_text = tk.Text(dline_params_frame)
        action_time_text.grid(row=3)

        consumers_autotranferible_label = tk.Label(dline_params_frame, text="Percentual de consumidores transferiveis instantaneamente para outra linha [%]", justify= 'left')
        consumers_autotranferible_label.grid(row=4)
        
        consumers_autotranferible_text = tk.Text(dline_params_frame)
        consumers_autotranferible_text.grid(row= 5)

        calculate_button = tk.Button(dline_params_frame, text='Calcular DEC')
        calculate_button.grid(row=6)
        

    def failure_selected(self, *args):
        # self.parameters_input_frame.destroy()
        index = self.failure_selection_cbox.current()
        order, failure_type = self.controller.get_failure_type(self.title, index)
        self.create_parameters_input_frame(order, failure_type)
        


class OutputNotebook:
    tab_collection = dict()

    def __init__(self, master: "View", controller, **kwargs):
        self.master = master
        self.controller = controller
        self.notebook = CustomNotebook(master)
        self.notebook.pack(pady=(8, 0), anchor="ne", fill="both", expand=True)
        self.add_table("Exemplo")
        cmd = self.notebook.register(self.on_tab_closed)
        self.notebook.bind("<<NotebookTabClosed>>", cmd + " %d")

    def add_table(self, title: str, view_table: pd.DataFrame | None = None):
        tab = tk.Frame(self.notebook)

        self.tab_collection[title] = tab

        tableWindow = tk.Frame(tab)

        if view_table is None:
            ntabLabel = tk.Label(
                tab, text="Seus outputs serão gerados aqui!", justify="left"
            )
            ntabLabel.pack(anchor="n", fill="x", expand=True)
        elif view_table.empty:
            return
        else:
            cols = list(view_table.columns)
            cols_len = len(cols)
            visable_cols = cols[0:3] + cols[3 + int((cols_len-5)/2):] # isso aqui seria garantia de emprego

            model = TableModel(view_table[visable_cols])
            self.table = MyCustonPandasTable(
                tableWindow, model=model, showtoolbar=True, editable=False
            )
            self.table.show()

            tableWindow.pack(anchor="n", fill="x")

            ttk.Separator(tab).pack(pady=5, fill="x", anchor="n")

            inputs_window = FailureTreatmentFrame(tab, self.controller, title, view_table)
            inputs_window.pack(anchor="n", fill="both")

        self.notebook.add(tab, text=title)
        self.notebook.select(tab)
        return

    def on_tab_closed(self, data):
        del self.tab_collection[data]
        if data != "Exemplo":
            self.controller.del_tab(data)


class View:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.status_bar = StatusBar(self.master, bg="white")
        self.options = tk.LabelFrame(self.master, text="Opções:")
        self.options.pack(side="left", fill="y", anchor="w")
        self.status_bar.set("Importe uma rede!")

    def set_controller(self, controller):
        self.controller = controller
        self.my__post__init__()

    def my__post__init__(self):
        self.create_menu()
        self.dec = DEC(self, self.options, self.controller)
        self.output = OutputNotebook(self.master, self.controller)

    def create_menu(self):
        menubar = tk.Menu(self.master, tearoff=False)
        self.master.config(menu=menubar)
        menubar.add_command(
            label="Importar",
            command=self.controller.import_file,
        )

    def askfilewindow(self):
        return tkinter.filedialog.askopenfilename(
            defaultextension=".PWF",
            filetypes=[("All files", "*"), ("Arquivo Texto do Anarede", ".PWF")],
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
            self.state(["pressed"])
            self._active = index
            return "break"

    def on_close_release(self, event):
        """Called when the button is released"""
        if not self.instate(["pressed"]):
            return

        element = self.identify(event.x, event.y)
        if "close" not in element:
            # user moved the mouse off of the close button
            return

        index = self.index("@%d,%d" % (event.x, event.y))

        if self._active == index:
            closed_tab_text = self.tab(index, "text")
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>", data=closed_tab_text)

        self.state(["!pressed"])
        self._active = None

    def __initialize_custom_style(self):
        style = ttk.Style()
        self.images = (
            tk.PhotoImage(
                "img_close",
                data="""
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                """,
            ),
            tk.PhotoImage(
                "img_closeactive",
                data="""
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs=
                """,
            ),
            tk.PhotoImage(
                "img_closepressed",
                data="""
                R0lGODlhCAAIAMIEAAAAAOUqKv9mZtnZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
            """,
            ),
        )

        style.element_create(
            "close",
            "image",
            "img_close",
            ("active", "pressed", "!disabled", "img_closepressed"),
            ("active", "!disabled", "img_closeactive"),
            border=8,
            sticky="",
        )
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.layout(
            "CustomNotebook.Tab",
            [
                (
                    "CustomNotebook.tab",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "CustomNotebook.padding",
                                {
                                    "side": "top",
                                    "sticky": "nswe",
                                    "children": [
                                        (
                                            "CustomNotebook.focus",
                                            {
                                                "side": "top",
                                                "sticky": "nswe",
                                                "children": [
                                                    (
                                                        "CustomNotebook.label",
                                                        {"side": "left", "sticky": ""},
                                                    ),
                                                    (
                                                        "CustomNotebook.close",
                                                        {"side": "left", "sticky": ""},
                                                    ),
                                                ],
                                            },
                                        )
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        )
