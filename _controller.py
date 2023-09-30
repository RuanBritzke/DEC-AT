import os
import view
from model import *


def save_to(directory=None, file_name=None, ext = None, automatic_process = True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            nonlocal directory, file_name
            if not automatic_process:
                if directory is None:
                    directory = view.choose_directory("Escolha o diretorio para salvar:")
                if file_name is None:
                    file_name = view.savefileas("Entre o nome do arquivo:",defaulfile = file_name, faultext = ext)
            file_path = os.path.join(directory, file_name)
            while True:
                try:
                    with open(file_path, 'w') as file:
                        file.write(value)
                except PermissionError as error:
                    message =f'{error }Por favor, feche o arquivo e então pressione "Enter" para continuar:'
                    view.print_temporary_message(message)
                    input()
                    continue
                return value
        return wrapper
    return decorator

def filter(*filterargs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            while True:
                value : str = func(*args, **kwargs)
                if any(arg_filter(value) if callable(arg_filter) else value.upper() == arg_filter.upper() for arg_filter in filterargs):
                    return value
                view.print_message(f"{value!r} incompativel com {*filterargs,!r}!")
        return wrapper
    return decorator


def repeatable(message : str = False, yes_answer : str = 'Y', no_answer: str = "N"):
    """Inputs:
    ==== 
        message: The message to write to the user e.g.: "Contiue? (Y/N)

        yes_answer: Answer that continues the loop e.g.: "Y"

        no_answer: Answer that breaks the loop e.g.: "N"
    """
    yn_input :str = filter(yes_answer, no_answer)(input)
    def decorator(func):
        def wrapper(*args, **kwargs):
            while True:
                if not message: continue
                value = func(*args, **kwargs)
                y_mask = yes_answer if yes_answer else 'Enter'
                repeat : str = yn_input(message + f" ({y_mask},{no_answer}): ")
                if repeat.upper() == yes_answer.upper():
                    continue
                elif repeat.upper() == no_answer.upper():
                    break
            return value
        return wrapper
    return decorator
#### - Literals - ####
CALLABLE: Literal = "CALLABLE"

#### - filtered_inputs - ####
def isalpha_filter(x): return str(x).isalpha()
def isint_filter(x):
    try:
        int(x)
        return True
    except:
        return False
def isfloat_filter(x):
    try:
        float(x)
        return True
    except:
        return False    
    
fltrd_aplha_input = filter(isalpha_filter)(input)
fltrd_float_input = filter(isfloat_filter)(input)
fltrd_int_input = filter(isint_filter)(input)


#### - utilities - ####
def merge_failure_tbl(dfs: list[pd.DataFrame]):
    df : pd.DataFrame = pd.concat(
        dfs,
        axis= 'index',
        ignore_index= True,
        )
    df.drop_duplicates(
        FAILURE,
        keep= 'first',
        ignore_index= True,
        inplace= True
    )
    df.sort_values(
        by = ORDER,
        axis= 'index',
        inplace= True,
        ignore_index= True
        )
    return df

def merge_paths(buses_paths: [list[list[tuple]]]):
    merged_paths = set()
    for paths in buses_paths:
        for path in paths:
            merged_paths.add(tuple(path))
    return [list(path) for path in merged_paths]

def output_to_csv(busnames, paths, target_names, failure_modes: pd.DataFrame):
    doc_string = f"Cargas;{';'.join(busnames)};\n"
    doc_string += "Fontes;" + ";".join(target_names) + ";\n"
    doc_string += "Matriz de Modos de Falha;\n"
    max_cols = 1
    max_cols = max([len(failures) for failures in failure_modes[FAILURE]])
    columns = list(failure_modes.columns)
    doc_string += f"index;{';'.join(columns)};\n"
    for row in failure_modes.itertuples():
        index = row[0]
        failures = row[1]
        failure = ";".join(failures)
        columns = [str(item) for item in row[2:]]
        doc_string += f"{index};{failure}{';'*(max_cols + 1 - len(failures))}{';'.join(columns)};\n"
    # doc_string += "Caminho;Trechos;\n"
    # inner = [f"{';'.join(path)};" for path in paths]
    # for i, path in enumerate(inner):
    #     new_str = "\n".join(path)
    #     doc_string += f"{i};{new_str};\n"
    return doc_string


def askfor_ld_params() -> dict:
    output = dict()
    output['ma'] = float(fltrd_float_input(
            f"\tPercentual de consumidores transferiveis via alimentadores MT por chave manual [%]: "))/100

    output['ta'] = float(fltrd_float_input(
            f"\tTempo para acionamento da chave para transferir a carga entre alimentadores [h]: "))
    output['md'] = float(fltrd_float_input(
            f"\tPercentual de consumidores transferiveis instantaneamente para outra linha [%]: "))/100
    return output

def askfor_a_params() -> dict:
    output = dict()
    output['ma'] = float(fltrd_float_input(
        f"\tPercentual de consumidores transferiveis via alimentadores MT por chave manual [%]: "))/100
    output['ta'] = float(fltrd_float_input(
        f"\tTempo para acionamento da chave para transferir a carga entre alimentadores [h]: "))
    output['md'] = float(fltrd_float_input(
        f"\tPercentual de consumidores transferiveis instantaneamente para outro trafos [%]: "))/100
    return output

def askfor_b_params() -> dict:
    output = dict()
    output['ma'] = float(fltrd_float_input(
        f"\tPercentual de consumidores transferiveis via alimentadores MT por chave manual [%]: "))/100
    output['ta'] = float(fltrd_float_input(
        f"\tTempo para acionamento da chave para transferir a carga entre alimentadores [h]: "))
    output['mc'] = float(fltrd_float_input(
        f"\tPercentual de consumidores transferiveis instantaneamente para outro trafos [%]: "))/100
    output['tc'] = float(fltrd_float_input(
        f"\tTempo para acionamento da chave para transferir a carga entre trafos [h]: "))
    output['md'] = float(fltrd_float_input(
        f"\tPercentual de consumidores transferiveis instantaneamente para outro trafos [%]: "))/100
    return output

def askfor_d_params() -> dict:
    output = dict()
    output['ma'] = float(fltrd_float_input(
        f"\tPercentual de consumidores transferiveis via alimentadores MT por chave manual [%]: "))/100
    output['ta'] = float(fltrd_float_input(
        f"\tTempo para acionamento da chave para transferir a carga entre alimentadores [h]: "))
    output['tc'] = float(fltrd_float_input(
        f"\tTempo para acionamento da chave para transferir a carga entre trafos [h]: "))
    output['md'] = float(fltrd_float_input(
        f"\tPercentual de consumidores transferiveis instantaneamente para outro trafos [%]: "))/100
    return output

topology = {
    'A': askfor_a_params, 
    'B': askfor_b_params, 
    'D': askfor_d_params, 
    }

def askfor_topology():
    topologies = "Topologias:\n"+"\n".join(topology.keys())
    view.print_message(topologies)
    option = filter(*topology.keys())(input)("Escolha a topologia dos transformadores: ").upper()
    return topology[option]()
 
#### - app controller - ####
class Controller:

    def __init__(self, model: Model) -> None:
        view.root = os.path.expanduser("~")
        self.model = model

    def initialize(self):
        self.load_pwf_file()
        self.model.create_net_from_pwf()
        self.main_menu()

    def load_pwf_file(self):
        view.ask_for_path()
        while True:
            pwf_path = view.choose_file('Escolha o arquivo PWF')
            view.print_message(pwf_path)
            if pwf_path.lower().endswith(".pwf"):
                break
            else:
                view.print_temporary_message(
                    f'''{pwf_path!r} não é do formato .pwf, escolha um arquivo .pwf
                    Pressione "Enter" para continuar.''')
                input()
        self.model.pwf_path = pwf_path

    def main_menu(self):
        while True:
            view.show_menu_options(self.menu_options_dict)
            option = filter(*self.menu_options_dict.keys())(input)("Escolha a opção: ").upper()
            self.menu_options_dict[option][CALLABLE](self)

    
    def saidi_per_failure(self, failure: list, order: int, group_cons: int):
        failure_names =", ".join([self.model.network.edges[edge][NAME] for edge in failure])
        view.print_message(failure_names)
        cons_hit = int(fltrd_int_input("Consumidores atingidos pela falha: "))
        if order > 1:
            ut = self.model.unavailability(failure)
            return cons_hit*ut/group_cons
        edge = failure[0] # unpack the edge
        if self.model.network.edges[edge][EDGE_TYPE] == LD:
            ut = self.model.unavailability(failure, **askfor_ld_params())
        else:
            ut = self.model.unavailability(failure, **askfor_topology())
        return cons_hit*ut/group_cons

    @repeatable(message="Repetir processo?", yes_answer="Y", no_answer="N")
    def saidi_per_substations(self):
        # raise NotImplementedError
        view.print_message("\nCalcular DEC por substação\n")
        sub = fltrd_aplha_input("Entre com a substação: ").upper()
        buses = self.model.get_load_buses_from_sub(sub)
        busnames = [self.model.get_bus_name(bus) for bus in buses]
        paths = merge_paths(self.model.paths_from_bus_to_sources(bus)
                            for bus in buses)
        targets = list({self.model.network.nodes[edge[1]][NAME] for edge in list({path[-1] for path in paths})})
        paths = [[self.model.network.edges[edge][NAME] for edge in path] for path in paths]
        message = "Barras encontradas: " + ", ".join([bus_name for bus_name in busnames])
        view.print_message(message)
        flr_table = merge_failure_tbl([self.model.failure_modes_table(bus) for bus in buses])
        if flr_table.empty:
            view.print_message(f"Nenhuma falha de ordem menor que 3 encontrada para {sub}")
            return
        else:
            flr_table_copy = flr_table.copy()
            flr_table_copy[FAILURE] = flr_table_copy[FAILURE].apply(
                lambda failure: "-".join([self.model.network.edges[edge][NAME] for edge in failure]))
            view.print_message(flr_table_copy.to_string())
        flr_table[UT] = 0 # creates the space to edit.
        flr_table[SAIDI] = 0
        group_cons = int(fltrd_int_input('Entre com o numero de consumidores do conjunto: '))
        for row in flr_table.itertuples():
            index = row[0]
            failure = row[1]
            order = row[2]
            flr_table.at[index, UT] = self.model.unavailability(failure)
            flr_table.at[index, SAIDI] = self.saidi_per_failure(failure, order, group_cons)

        flr_table[FAILURE] = flr_table[FAILURE].apply(
            lambda failure: [self.model.network.edges[edge][NAME] for edge in failure])
        save_to_csv = save_to(directory= "~\Desktop", automatic_process=False)(output_to_csv)
        save_to_csv(busnames, paths, targets, flr_table)

    def saidi_all_susbstation(self):
        view.print_message("Selecione o diretório para salvar os arquivos:")
        directory = view.choose_directory("Selecione o diretório")
        view.print_message(directory)
        sub : str
        buses : list[int]
        for i, (sub, buses) in enumerate(self.model.load_substations_dict.items()):
            busnames: list[str] = [self.model.network.nodes[bus][NAME] for bus in buses]
            view.print_front_message(
                f"{i+ 1} Colentando informações para {sub}")
            paths = merge_paths(self.model.paths_from_bus_to_sources(bus) for bus in buses)
            targets = list({self.model.network.nodes[edge[1]][NAME] for edge in  list({path[-1] for path in paths})})
            paths = [[self.model.network.edges[edge][NAME] for edge in path] for path in paths]
            flr_modes_tbl = merge_failure_tbl(self.model.failure_modes_table(bus) for bus in buses)
            if flr_modes_tbl.empty:
                view.print_message(
                    f"Nenhuma falha de ordem menor que 3 encontrada em ({sub})!")
                continue
            flr_modes_tbl[UT] = flr_modes_tbl[FAILURE].apply(lambda failure: self.model.unavailability(failure))
            flr_modes_tbl[FAILURE] = flr_modes_tbl[FAILURE].apply(lambda failure: [self.model.network.edges[edge][NAME] for edge in failure])
            save_to_csv = save_to(directory, file_name= f"Substacao {sub.replace('/','-')}.csv")(output_to_csv)
            save_to_csv(busnames, paths, targets, flr_modes_tbl)
            break
        view.print_message("Processo encerrado com sucesso!")
        view.erase_last_line()

    def app_exit(self):
        exit()

    menu_options_dict = {
        "1": {
            CALLABLE: saidi_per_substations,
            NAME : 'Calcular DEC por subestação'},
        "2": {
            CALLABLE: saidi_all_susbstation,
            NAME: 'Calcular DEC para todas subestações'},
        "Q": {
            CALLABLE: app_exit,
            NAME: 'Sair'
        }
    }

def main():
    model = Model()
    controller = Controller(model)
    controller.initialize()


if __name__ == "__main__":
    main()
