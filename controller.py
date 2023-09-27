import os

from model import *
from view import *

ALL = "All"
SE = "SE"
BUS = "BUS"


class Controller:
    view_tab_collection = dict()
    view = None

    def __init__(self, model: Model, view: View):
        self.model = model
        self.view = view

        self.view.set_controller(self)

    def import_file(self):
        file = self.view.askfilewindow()
        file_ext = os.path.splitext(file)[-1]
        if file_ext != ".PWF":
            self.view.status_bar.set(f'FALHA! Extensão não aceita: "{file_ext}"')
        else:
            self.view.status_bar.set(f'Importando aquivo de: "{file}"')
            buses, lines = self.model.create_net(file)
            self.view.status_bar.set(
                f"Rede importada: {buses} Barras e {lines} conexões!"
            )
            self.view.dec.enable()

    def get_options_cbox_values(self, to: Literal["SUB", "BUS"]):
        if to == SUB:
            return sorted(self.model.load_subs)
        elif to == BUS:
            return sorted(self.model.load_buses)
        else:
            return None

    def processingData(self, indexes: list, data: list, sub, buses):
        visited_failures = set()
        for bus in sorted(
            buses,
            key=lambda x: self.model.network.nodes[x][VOLTAGE_LEVEL],
            reverse=True,
        ):
            failureModes = self.model.failure_modes_table(bus)
            for index, failures, _ in failureModes.itertuples():
                if failures in visited_failures:
                    continue
                indexes.append((sub, bus, index))
                data.append([list(failures)])
                visited_failures.add(failures)
        return indexes, data

    def generateFailureTable(
        self, scope: Literal["ALL", "SE", "SUB"], entry: str | int | None = None
    ):
        indexes = list()
        data = list()
        if scope == ALL:
            for kw, buses in self.model.load_subs_dict.items():
                indexes, data = self.processingData(indexes, data, kw, buses)

        elif scope == SE:
            buses = self.model.load_subs_dict[entry]
            indexes, data = self.processingData(indexes, data, entry, buses)

        elif scope == BUS:
            sub = self.model.network.nodes[entry][SUB]
            indexes, data = self.processingData(indexes, data, sub, [entry])

        mi = pd.MultiIndex.from_tuples(indexes, names=["SE", "BARRA", "N"])
        df = pd.DataFrame(data, index=mi, columns=["FALHAS"])
        maxFailureLen = df["FALHAS"].apply(len).max()

        for i in range(maxFailureLen):
            df[f"_FALHA_{i+1}"] = df["FALHAS"].apply(
                lambda x: x[i] if len(x) > i else None
            )
        df.drop(columns="FALHAS", inplace=True)

        flatDf = df.reset_index()
        return flatDf

    def computeUnavailabilty(self, entry: str | None = None):
        if entry in self.view_tab_collection.keys():
            old_tab = self.view.output.tab_collection[entry][0]
            self.view.output.notebook.select(old_tab)
            return
        if entry == "Todas SEs":
            df = self.generateFailureTable(scope=ALL)
        elif entry.isalpha():
            df = self.generateFailureTable(scope=SE, entry=entry)
        elif entry.isnumeric():
            df = self.generateFailureTable(scope=BUS, entry=int(entry))
        else:
            raise ValueError(f"entry value: {repr(entry)} isn't expected")
        df["N"] = df["N"] + 1
        df = self.view_table(df)

        for row in df.itertuples():
            maxorder = (len(row[1:]) - 3)/2
            index = row[0]
            failures = self.treat_failures(row[4:int(4+maxorder)])[0]
            df.at[index, "IND"] = self.model.unavailability(failures)
            df.at[index, "DEC"] = None
            
        self.view_tab_collection[entry] = df
        print(f"add_title(title = {entry}, view_table={df}") # Debugging
        self.view.output.add_table(title=f"{entry}", view_table=df)

    def view_table(self, view_table: pd.DataFrame):
        for col in view_table.columns[3:]:  # iterate over all failure columns
            new_col = " ".join(col.split("_"))
            
            view_table[new_col] = view_table[col].map(
                self.model.get_edge_name, na_action="ignore"
            )
        return view_table
    
    def compute_dec(self,*, entry:str, index:int, **kwargs:dict):
        print(f"compute_dec(entry= {entry}, index= {index}, kwargs= {kwargs})")
        dec = self.model.compute_dec(**kwargs)
        df : pd.DataFrame = self.view_tab_collection[entry]
        df.at[index,'DEC'] = dec
        self.view.output.update_table(self.view.output.tab_collection[entry][1], df)
        return

    def treat_failures(self, failures):
        failures = [fail for fail in failures if fail is not None]
        return failures, len(failures)

    def del_tab(self, entry):
        del self.view_tab_collection[entry]

    def get_failure_atts(self, entry, index):
        df = self.view_tab_collection[entry]
        row = df.iloc[index].to_list()
        maxorder = (len(row[0:]) - 5)/2
        failures, order = self.treat_failures(row[3:int(3+maxorder)])
        if order == 1:
            edge = failures[0]
            return failures, order, self.model.network.edges[edge][EDGE_TYPE]
        if order == 2:
            edge1 = failures[0]
            edge2 = failures[1]
            return failures, order, (self.model.network.edges[edge1][EDGE_TYPE], self.model.network.edges[edge2][EDGE_TYPE])