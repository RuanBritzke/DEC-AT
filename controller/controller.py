import os

from model import *
from view import *
from utils import functions

ALL = "All"
SE = "SE"
BUS = "BUS"


class Controller:
    view_tab_collection = dict()
    view = None

    def __init__(self, view: View):
        self.view = view

        self.view.set_controller(self)

    def import_pwf_file(self):
        file = functions.resource_path(self.view.askfilewindow())
        file_ext = os.path.splitext(file)[-1]
        if file_ext != ".PWF":
            self.view.status_bar.set(f'FALHA! Extensão não aceita: "{file_ext}"')
        else:
            self.view.status_bar.set(f'Importando redes de: "{file}"')

            self.model = Model.from_pwf(file)
            self.view.status_bar.set(
                f"Rede importada: {len(self.model.nodes)} Barras e {len(self.model.edges)} conexões!"
            )
            self.view.input_options.enable()

    def import_bus_data(self):
        if not hasattr(self, "model"):
            self.view.alert("Primeiro importe um arquivo PWF!")
            return
        file = functions.resource_path(self.view.askfilewindow())
        file_ext = os.path.splitext(file)[-1]
        if file_ext != ".csv":
            self.view.alert(f'FALHA! Extensão não aceita: "{file_ext}"')
        else:
            self.view.status_bar.set(f'Importando dados de: "{file}"')
            self.model.bus_data = bus_data(file)

    def import_edge_data(self):
        if not hasattr(self, "model"):
            self.view.alert("Primeiro importe um arquivo PWF!")
            return
        file = functions.resource_path(self.view.askfilewindow())
        file_ext = os.path.splitext(file)[-1]
        if file_ext != ".csv":
            self.view.alert(f'FALHA! Extensão não aceita: "{file_ext}"')
        else:
            self.view.status_bar.set(f'Importando dados de: "{file}"')
            self.model.edge_data = edge_data(file)

    def get_options_cbox_values(self, to: Literal["SUB", "BUS"]):
        if to == SUB:
            return sorted(self.model.load_subs)
        elif to == BUS:
            return sorted(self.model.load_buses)
        else:
            return None

    def get_model_bars(self) -> list | None:
        if hasattr(self, "model"):
            return list(self.model.nodes)
        return None

    def generate_failure_table(
        self,
        scope: Literal["ALL", "SE", "SUB"],
        entry: str | int | None = None,
        target: str | int = None,
    ):
        indexes = list()
        if scope == ALL:
            for kw, buses in self.model.load_subs_dict.items():
                indexes, data = self.processing_data(indexes, kw, buses, target)

        elif scope == SE:
            buses = self.model.load_subs_dict[entry]
            indexes, data = self.processing_data(indexes, entry, buses, target)

        elif scope == BUS:
            entry = int(entry)
            sub = self.model.nodes[entry][SUB]

            indexes, data = self.processing_data(indexes, sub, [entry], target)

        mi = pd.MultiIndex.from_tuples(indexes, names=["SE", "BARRA DE CARGA", "N"])
        df = pd.DataFrame(data, index=mi, columns=["FALHAS"])

        if df.empty:
            return df.reset_index()

        maxFailureLen = df["FALHAS"].apply(len).max()
        for i in range(maxFailureLen):
            df[f"_FALHA_{i+1}"] = df["FALHAS"].apply(
                lambda x: x[i] if len(x) > i else None
            )
        df.drop(columns="FALHAS", inplace=True)
        flatDf = df.reset_index()
        return flatDf

    def processing_data(self, indexes: list, sub, buses: list, target=None):
        visited_failures = set()
        data = list()
        for bus in sorted(
            buses,
            key=lambda x: self.model.nodes[x][VOLTAGE_LEVEL],
            reverse=True,
        ):
            failureModes = self.model.failure_modes_table(bus, targets=[target])
            for index, failures, _ in failureModes.itertuples():
                if failures in visited_failures:
                    continue
                indexes.append((sub, bus, index))
                data.append([list(failures)])
                visited_failures.add(failures)
        return indexes, data

    def compute_unavailabilty(
        self, scope, origin: int | str | None = None, target: str | None = None
    ):
        if origin in self.view_tab_collection.keys():
            old_tab = self.view.output.tab_collection[origin][0]
            self.view.output.notebook.select(old_tab)
            return
        if scope == "Todas SEs":
            df = self.generate_failure_table(ALL, target)
        elif scope == "SUB":
            df = self.generate_failure_table(SE, origin, target)
        elif scope == "BUS":
            df = self.generate_failure_table(BUS, int(origin), target)
        else:
            raise ValueError(f"Origin value: {repr(origin)} isn't expected")
        df = self.view_table(df)

        for row in df.itertuples():
            maxorder = (
                len(row[1:]) - 2
            ) / 2  # SE BARRA ORDEM (FALHA_i -> n) (FALHA i -> n)
            index = row[0]
            failures, _ = self.treat_failures(row[3 : int(3 + maxorder)])
            U = self.model.unavailability(failures)
            df.at[index, "U"] = U

        df = df.loc[df["U"] != 0]
        df = df.reset_index()
        df = df[df.columns[1:]]

        self.view_tab_collection[origin] = df
        self.view.output.add_table(title=f"{origin}", view_table=df)

    def view_table(self, view_table: pd.DataFrame):
        for col in view_table.columns[3:]:  # iterate over all failure columns
            new_col = " ".join(col.split("_"))

            view_table[new_col] = view_table[col].map(
                self.model.get_element_name, na_action="ignore"
            )
        view_table.drop(["N"], axis="columns", inplace=True)
        return view_table

    def calculate_params(
        self,
        *,
        entry: str,
        index: int,
        failures: Iterable,
        group_consumers: int,
        hit_consumers: int,
        avg_load: float = 0,
        max_load: float = 0,
        ma: float = 0,
        mc: float = 0,
        md: float = 0,
        ta: float = 0,
        tc: float = 0,
        **kwargs,
    ):
        ma = ma / 100
        mc = mc / 100
        md = md / 100
        ta = ta
        tc = tc

        if group_consumers == 0:
            group_consumers = 1
        if hit_consumers == 0:
            hit_consumers = group_consumers

        df: pd.DataFrame = self.view_tab_collection[entry]

        dec = self.model.calculate_dec(
            failures=failures,
            group_consumers=group_consumers,
            hit_consumers=hit_consumers,
            ma=ma,
            mc=mc,
            md=md,
            ta=ta,
            tc=tc,
        )
        fec = self.model.calculate_fec(
            failures=failures,
            group_consumers=group_consumers,
            hit_consumers=hit_consumers,
            md=md,
        )
        df.at[index, "DEC"] = dec

        df.at[index, "FEC"] = fec

        df.at[index, "EMND MÉDIA"], df.at[index, "EMND MÁXIMA"] = (
            self.model.calculate_ens(dec=dec, avg_load=avg_load, max_load=max_load)
        )

        self.view.output.update_table(self.view.output.tab_collection[entry][1], df)

    def del_tab(self, entry):
        del self.view_tab_collection[entry]

    def get_failure_atts(self, entry, index):
        df: pd.DataFrame = self.view_tab_collection[entry]
        failures_columns = [col for col in df.columns.to_list() if "_FALHA" in col]
        failures = df[failures_columns].iloc[index].to_list()
        failures, order = self.treat_failures(failures)
        if order == 1:
            if isinstance(failures[0], int):
                return failures, order, self.model.nodes[failures[0]][BUS_TYPE]
            return failures, order, self.model.edges[failures[0]][EDGE_TYPE]
        if order == 2:
            failure_atts = list()
            for failure in failures:
                if isinstance(failure, int):
                    failure_atts.append(self.model.nodes[failure][BUS_TYPE])
                else:
                    failure_atts.append(self.model.edges[failure][EDGE_TYPE])
            return failures, order, failure_atts

    def treat_failures(self, failures) -> tuple:
        failures = [fail for fail in failures if fail is not None]
        return failures, len(failures)

    # def separete_failures(self, entry, index, order):
    #     new_df: pd.DataFrame = self.view_tab_collection[entry].copy()
    #     self.del_tab(entry)
    #     new_df.loc[new_df.index > index, "N"] += order - 1
    #     failure_cols = [col for col in new_df.columns if col.startswith("_FALHA_")]
    #     new_df = new_df[["SE", "BARRA", "N"] + failure_cols]
    #     failure_elements_list = new_df.loc[index, failure_cols].to_list()
    #     for i, failure_element in enumerate(failure_elements_list):
    #         new_row = {
    #             "SE": [new_df.at[index, "SE"]],
    #             "BARRA": [new_df.at[index, "BARRA"]],
    #             "N": [new_df.at[index, "N"] + i + 1],
    #             "_FALHA_1": [failure_element],
    #         }
    #         new_df = pd.concat(
    #             [new_df, pd.DataFrame(new_row, index=[0])], ignore_index=True
    #         )
    #     # new_df.drop(index, inplace=True)
    #     new_df.replace(np.nan, None, inplace=True)
    #     new_df.sort_values("N", axis="index", inplace=True)
    #     new_df.reset_index(drop=True, inplace=True)
    #     new_df = self.view_table(new_df)
    #     for row in new_df.itertuples():
    #         maxorder = (len(row[1:]) - 3) / 2
    #         index = row[0]
    #         failures, order = self.treat_failures(row[4 : int(4 + maxorder)])
    #         if order == 1:
    #             new_df.at[index, "Up"] = self.model.unavailability_p(*failures)
    #             new_df.at[index, "Ut"] = self.model.unavailability_t(*failures)

    #     self.view_tab_collection[entry] = new_df
    #     self.view.output.update_table(self.view.output.tab_collection[entry][1], new_df)
    #     self.view.output
    #     return
