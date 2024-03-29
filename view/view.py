import pandas as pd

from icecream import ic
from tkinter import filedialog
from tkinter import messagebox

from view.widgets import *
from utils.contants import *

pd.options.mode.chained_assignment = None  # default='warn'


class View:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.status_bar = StatusBar(self.master, bg="white")
        self.options = tk.LabelFrame(self.master, text="Opções:")
        self.options.pack(side="left", fill="y", anchor="w")
        self.status_bar.set("Importe uma rede!")
        self.startup_alert()

    def alert(self, message):
        messagebox.showerror("Erro!", message)

    def startup_alert(self):
        messagebox.showinfo("Olá", "Para iniciar o estudo, importe um arquivo PWF!")

    def set_controller(self, controller):
        self.controller = controller
        self.my__post__init__()

    def my__post__init__(self):
        self.create_menu()
        self.input_options = InputOptions(self, self.options, self.controller)
        self.output = OutputNotebook(self.master, self.controller)

    def create_menu(self):
        menu_bar = tk.Menu(self.master, tearoff=False)
        import_menu = tk.Menu(menu_bar, tearoff=False)
        import_menu.add_command(
            label="Dados Barras", command=self.controller.import_bus_data
        )
        import_menu.add_command(
            label="Dados Conexoes", command=self.controller.import_edge_data
        )
        import_menu.add_separator()
        import_menu.add_command(label="PWF", command=self.controller.import_pwf_file)
        menu_bar.add_cascade(label="Importar", menu=import_menu)
        self.master.config(menu=menu_bar)

    def askfilewindow(self):
        return filedialog.askopenfilename(
            defaultextension=".PWF",
            filetypes=[("All files", "*"), ("Arquivo Texto do Anarede", ".PWF")],
            initialdir="~",
        )


class InputOptions(tk.Frame):
    cbox_values = None
    target_cbox_values = None

    def __init__(self, root, master, controller, **kwargs):
        self.root = root
        self.master = master
        self.controller = controller
        super().__init__(master, **kwargs)
        self.create_target_selection_box()
        self.create_function_selection_buttons()
        self.create_origin_selection_box()
        self.pack(anchor="nw")
        ttk.Separator(master).pack(pady=5, fill="x", anchor="n")

    def create_target_selection_box(self):
        tk.Label(self, text="Selecione Barra Alvo").pack(anchor="nw")
        root = tk.Frame(self)
        self.target_cbox_var = tk.StringVar()
        self.target_cbox = ttk.Combobox(
            root,
            state="disabled",
            textvariable=self.target_cbox_var,
            postcommand=self.update_target_cbox_list,
        )
        self.target_cbox.grid(row=0, column=0, padx=5, pady=5)
        root.pack(fill="x", expand=True)

    def update_target_cbox_list(self):
        self.target_cbox["values"] = ["-"] + self.controller.get_model_bars()

    def create_function_selection_buttons(self):
        labels = ["Todas SEs", "Por SE", "Por BARRA"]
        self.radiovar = tk.IntVar()
        for i, label in enumerate(labels):
            self.radio_btn = tk.Radiobutton(
                self,
                text=label,
                state="disabled",
                variable=self.radiovar,
                value=i,
                command=lambda: self.radio_button_selection(self.radiovar.get()),
            )
            self.radio_btn.pack(anchor="nw")
        self.origin_cbox_values = "Todas SEs"
        self.radiovar.set(0)
        self.searchscope = "Todas SEs"

    def radio_button_selection(self, option: int):
        if option == 0:
            self.origin_cbox.config(state="disabled")
            self.origin_cbox_values = "Todas SEs"
            self.origin_cbox.set("Todas SEs")
            self.searchscope = "Todas SEs"

        if option == 1:
            self.origin_cbox.config(state="normal")
            self.origin_cbox_values = self.controller.get_options_cbox_values(to=SUB)
            self.origin_cbox.set(self.origin_cbox_values[0])
            self.searchscope = "SUB"

        elif option == 2:
            self.origin_cbox.config(state="normal")
            self.origin_cbox_values = self.controller.get_options_cbox_values(to=BUS)
            self.origin_cbox.set(self.origin_cbox_values[0])
            self.searchscope = "BUS"

    def create_origin_selection_box(self):
        tk.Label(self, text="Calcular DEC:").pack(anchor="nw")
        root = tk.Frame(self)
        self.origin_cbox_var = tk.StringVar()
        self.origin_cbox = ttk.Combobox(
            root,
            state="disabled",
            textvariable=self.origin_cbox_var,
            postcommand=self.update_origin_cbox_list,
        )
        self.origin_cbox.grid(row=0, column=0, padx=5, pady=5)
        self.search = tk.Button(root, text="Procurar", state="disabled")
        self.search.grid(row=0, column=1, padx=5, pady=5)
        root.pack(fill="x", expand=True)
        self.search.bind("<ButtonRelease-1>", self.start_search)
        self.origin_cbox.set("Todas as SEs")
        self.origin_cbox.config(state="disabled")

    def update_origin_cbox_list(self):
        self.origin_cbox["values"] = self.origin_cbox_values

    def start_search(self, *args):
        self.root.status_bar.set(
            f"Calculando Indisponibilidade para {self.origin_cbox.get()}"
        )
        self.controller.compute_unavailabilty(
            self.searchscope,
            self.origin_cbox.get(),
            int(self.target_cbox.get()),
        )
        self.root.status_bar.set("Pronto!")

    def enable(self, _state="normal"):
        def set_state(widget: tk.Widget):
            for ch in widget.winfo_children():
                set_state(ch)
            if "state" in widget.keys():
                widget.config(state=_state)

        set_state(self)

    def disable(self):
        self.enable("disable")


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

        tableWindow = tk.Frame(tab)

        if view_table is None:
            ntabLabel = tk.Label(
                tab, text="Seus outputs serão gerados aqui!", justify="left"
            )
            ntabLabel.pack(anchor="n", fill="x", expand=True)
            self.tab_collection[title] = (tab, ntabLabel)

        elif view_table.empty:
            ntabLabel = tk.Label(tab, text="Nenhuma saída gerada", justify="left")
            ntabLabel.pack(anchor="n", fill="x", expand=True)
            self.tab_collection[title] = (tab, ntabLabel)
        else:
            visable_cols = (col for col in view_table.columns if "_FALHA_" not in col)
            model = TableModel(view_table[visable_cols])
            table = MyCustonPandasTable(
                tableWindow, model=model, showtoolbar=True, editable=False
            )

            self.tab_collection[title] = (tab, table)
            table.show()
            tableWindow.pack(anchor="n", fill="x")

            ttk.Separator(tab).pack(pady=5, fill="x", anchor="n")
            self.inputs_window = FailureTreatmentFrame(
                tab, self.controller, title, view_table
            )
            self.inputs_window.pack(anchor="n", fill="both")

        self.notebook.add(tab, text=title)
        self.notebook.select(tab)
        return

    def on_tab_closed(self, data):
        del self.tab_collection[data]
        if data != "Exemplo":
            self.controller.del_tab(data)

    def update_table(self, table: MyCustonPandasTable, new_data: pd.DataFrame):
        visable_cols = (col for col in new_data.columns if "_FALHA_" not in col)
        self.inputs_window.view_table = new_data
        table.updateModel(TableModel(new_data[visable_cols]))
        table.redraw()


class FailureTreatmentFrame(tk.Frame):
    arguments = dict()

    def __init__(self, master, controller, title, view_table: pd.DataFrame, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.title = title
        self.arguments["entry"] = self.title
        self.view_table = view_table
        self.create_widgets()
        return

    def create_widgets(self):
        self.create_consumer_units_in_set_frame()
        self.create_demand_unput_in_set_frame()
        self.create_failure_selection_frame()
        return self

    def create_consumer_units_in_set_frame(self):
        consumer_units_in_set_frame = tk.Frame(self)
        consumer_units_in_set_frame.pack(anchor="nw", fill="x", expand="True")
        self.consumer_units_in_set_form = Form(
            consumer_units_in_set_frame,
            {
                "group_consumers": "Número de unidades consumidoras do conjunto",
                "hit_consumers": "Número de unidades consumidoras atingidas",
            },
        )
        self.consumer_units_in_set_form.pack(anchor="nw", fill="x", expand="True")
        return self
    
    def create_demand_unput_in_set_frame(self):
        demand_in_set_frame = tk.Frame(self)
        demand_in_set_frame.pack(anchor="nw", fill="x", expand="True")
        self.demand_in_set_frame_form = Form(
            demand_in_set_frame, 
            {
                "avg_load" : "Demanda Média do Ponto de Carga",
                "max_load" : "Demanda Máxima do Ponto de Carga"
            }
        )
        self.demand_in_set_frame_form.pack(anchor="nw", fill="x", expand="True")


    def create_failure_selection_frame(self):
        failure_selection_frame = tk.Frame(self)
        failure_selection_frame.columnconfigure(0, weight=8, minsize=80)
        failure_selection_frame.columnconfigure(1, weight=1, minsize=35)
        failure_selection_frame.pack(anchor="nw", fill="x", expand=True)

        failure_selection_label = tk.Label(
            failure_selection_frame,
            text="Selecione a Falha:",
            anchor="w",
            justify="left",
        )
        failure_selection_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.failure_vars = tk.StringVar()

        self.failure_selection_cbox = ttk.Combobox(
            failure_selection_frame,
            textvariable=self.failure_vars,
            postcommand=self.update_failures_list,
        )

        cmd = self.failure_selection_cbox.register(self.failure_selected)
        self.failure_selection_cbox.bind("<<ComboboxSelected>>", cmd)
        # Tem que ser assim pra funcionar, não sei por que.
        self.failure_selection_cbox.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.failure_selection_cbox.set("Falha")

    def update_failures_list(self):
        substring = "FALHA "
        fail_cols = [col for col in self.view_table.columns if substring in col]
        self.failure_selection_cbox["values"] = (
            self.view_table[fail_cols]
            .apply(lambda row: " <-> ".join(filter(None, row)), axis=1)
            .tolist()
        )

    def failure_selected(self, *args):
        index = self.failure_selection_cbox.current()
        failures, order, failure_type = self.controller.get_failure_atts(
            self.title, index
        )
        self.arguments["index"] = index
        self.arguments["failures"] = failures
        self.create_parameters_input_frame(order, failure_type)

    def create_parameters_input_frame(
        self, order: int, failure_type: str | tuple[str, str]
    ):
        if (
            hasattr(self, "parameters_input_frame")
            and self.parameters_input_frame.winfo_exists()
        ):
            self.parameters_input_frame.destroy()

        self.parameters_input_frame = tk.Frame(self)
        if failure_type is None:
            return
        else:
            if order == 1:
                if failure_type == XFMR:
                    self.create_xfmr_topology_frame(master=self.parameters_input_frame)
                else:  # failure_type == DLIN:
                    self.topology_selected(
                        master=self.parameters_input_frame, failure_type=DLIN
                    )
            if order == 2:
                # self.create_failure_separator(master=self.parameters_input_frame)
                self.topology_selected(
                    master=self.parameters_input_frame, failure_type=DLIN
                )
            self.parameters_input_frame.pack(anchor="center", fill="both", expand=True)

    # def create_failure_separator(self, *, master):
    #     failure_separator = tk.Frame(master)
    #     failure_separator.columnconfigure(0, weight=8, minsize=80)
    #     failure_separator.columnconfigure(1, weight=1, minsize=35)
    #     failure_separator.pack(anchor="ne", fill="both", expand=True)

    #     failure_separator_description = tk.Label(
    #         failure_separator,
    #         text="Caso um elemento da falha não suportar toda a carga, separe a falha.",
    #         anchor="w",
    #         justify="left",
    #     )
    #     failure_separator_description.grid(
    #         row=0, column=0, padx=5, pady=5, sticky="nsew"
    #     )

    #     failure_separator_button = tk.Button(
    #         failure_separator,
    #         text="Separar Falha",
    #         command=self.send_separate_failure_command,
    #     )
    #     failure_separator_button.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

    # def send_separate_failure_command(self):
    #     self.controller.separete_failures(
    #         self.arguments["entry"],
    #         self.arguments["index"],
    #         len(self.arguments["failures"]),
    #     )

    def create_xfmr_topology_frame(self, master):
        xfmr_topology_frame = tk.Frame(master)
        xfmr_topology_frame.columnconfigure(0, weight=8, minsize=80)
        xfmr_topology_frame.columnconfigure(1, weight=1, minsize=35)
        xfmr_topology_frame.pack(anchor="ne", fill="both", expand=True)

        xfmr_topology_cbox_label = tk.Label(
            xfmr_topology_frame,
            text="Selecione a Topologia do Transformador:",
            anchor="w",
            justify="left",
        )
        xfmr_topology_cbox_label.grid(
            row=0, column=0, padx=(5, 0), pady=5, sticky="nsew"
        )

        self.topology_var = tk.StringVar()
        self.xfmr_topology_cbox = ttk.Combobox(
            xfmr_topology_frame,
            textvariable=self.topology_var,
            values=["A", "B", "C", "D"],
        )
        self.xfmr_topology_cbox.set("Topologias")
        self.xfmr_topology_cbox.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # binding function to combobox selection
        self.xfmr_topology_cbox.bind(
            "<<ComboboxSelected>>",
            lambda event: self.topology_selected(
                master=self.parameters_input_frame,
                failure_type=self.xfmr_topology_cbox.current(),
            ),
        )
        return

    failure_types = {
        DLIN: [1, ("md", "ma", "ta")],
        0: [1, ("md", "ma", "ta")],  # 0 = A : beta = 1
        1: [2, ("md", "ma", "ta", "mc", "tc")],  # 1 = B : beta = 2
        2: [2, ("md", "ma", "ta", "mc", "tc")],  # 2 = C : beta = 2
        3: [1, ("md", "ma", "ta")],  # 3 = D : beta = 1
    }

    param_prompt_dict = {
        "md": "Percentual de consumidores transferíveis instantaneamente para outro(a) transformador/linha (DJ via AT), ou por TA (via MT) [%]",
        "ma": "Percentual de consumidores transferíveis manualmente via alimentadores MT de outras subestações via chaveamento [%]",
        "ta": "Tempo de acionamento manual da(s) chave(s) para transferir a carga para alimentadores de outras subestações [h]",
        "mc": "Percentual de consumidores transferíveis manualmente para outro transformador da mesma subestação via chaveamento [%]",
        "tc": "Tempo de acionamento manual da(s) chave(s) para isolar o defeito e transferir a carga entre transformadores da mesma subestação [h]",
    }

    # Construtor de formulário
    def topology_selected(
        self, *, master: tk.Frame | None = None, failure_type: str | None = None
    ):
        if hasattr(self, "formulary") and self.formulary.container.winfo_exists():
            self.formulary.destroy()
        if (
            hasattr(self, "calculate_button")
            and self.calculate_button.winfo_exists()
        ):
            self.calculate_dec_button.destroy()

        self.arguments["beta"] = self.failure_types[failure_type][0]
        prompts = {
            key: self.param_prompt_dict[key]
            for key in self.failure_types[failure_type][1]
        }

        self.formulary = Form(master, prompts)
        self.formulary.pack(side="top", anchor="nw", fill="x", expand="true")

        self.calculate_button = tk.Button(
            master, text="Calcular Parametros", command=self.send_params
        )
        self.calculate_button.pack(side="bottom", anchor="se", padx=5)
        return

    def send_params(self):
        self.arguments.update(self.consumer_units_in_set_form.get_entry_values())
        self.arguments.update(self.demand_in_set_frame_form.get_entry_values())
        self.arguments.update(self.formulary.get_entry_values())
        self.controller.calculate_params(**self.arguments)
        return
