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

    def import_file(self):
        file = functions.resource_path(self.view.askfilewindow())
        file_ext = os.path.splitext(file)[-1]
        if file_ext != ".PWF":
            self.view.status_bar.set(f'FALHA! Extensão não aceita: "{file_ext}"')
        else:
            self.view.status_bar.set(f'Importando aquivo de: "{file}"')

            self.model = Model.from_pwf(file)
            self.view.status_bar.set(
                f"Rede importada: {len(self.model.nodes)} Barras e {len(self.model.edges)} conexões!"
            )
            self.view.input_options.enable()

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
        data = list()
        if scope == ALL:
            for kw, buses in self.model.load_subs_dict.items():
                indexes, data = self.processing_data(indexes, data, kw, buses, target)

        elif scope == SE:
            buses = self.model.load_subs_dict[entry]
            indexes, data = self.processing_data(indexes, data, entry, buses, target)

        elif scope == BUS:
            entry = int(entry)
            sub = self.model.nodes[entry][SUB]

            indexes, data = self.processing_data(indexes, data, sub, [entry], target)

        ic(indexes)
        ic(data)

        mi = pd.MultiIndex.from_tuples(indexes, names=["SE", "BARRA", "N"])
        df = pd.DataFrame(data, index=mi, columns=["FALHAS"])

        if df.empty:
            return df.reset_index()

        maxFailureLen = df["FALHAS"].apply(len).max()
        ic(df)
        ic(maxFailureLen)

        for i in range(maxFailureLen):
            df[f"_FALHA_{i+1}"] = df["FALHAS"].apply(
                lambda x: x[i] if len(x) > i else None
            )
        df.drop(columns="FALHAS", inplace=True)
        flatDf = df.reset_index()
        return flatDf

    def processing_data(self, indexes: list, data: list, sub, buses: list, target=None):
        visited_failures = set()
        for bus in sorted(
            buses,
            key=lambda x: self.model.nodes[x][VOLTAGE_LEVEL],
            reverse=True,
        ):
            failureModes = self.model.failure_modes_table(bus, targets=[target])
            ic(failureModes)
            for index, failures, _ in failureModes.itertuples():
                if failures in visited_failures:
                    continue
                indexes.append((sub, bus, index))
                data.append([list(failures)])
                visited_failures.add(failures)
        return indexes, data

    def compute_unavailabilty(
        self, scope, origin: str | None = None, target: str | None = None
    ):
        ic(scope, origin, target)
        if origin in self.view_tab_collection.keys():
            old_tab = self.view.output.tab_collection[origin][0]
            self.view.output.notebook.select(old_tab)
            return
        if scope == "Todas SEs":
            df = self.generate_failure_table(ALL, target)
        elif scope == "SUB":
            df = self.generate_failure_table(SE, origin, target)
        elif scope == "BUS":
            origin = origin.split()[0]
            df = self.generate_failure_table(BUS, origin, target)
        else:
            raise ValueError(f"Origin value: {repr(origin)} isn't expected")
        df["N"] = df["N"] + 1
        df = self.view_table(df)

        for row in df.itertuples():
            maxorder = (
                len(row[1:]) - 3
            ) / 2  # N SE BARRA ORDEM (FALHA_i -> n) (FALHA i -> n)
            index = row[0]
            failures = self.treat_failures(row[4 : int(4 + maxorder)])[0]
            try:
                df.at[index, "IND"] = self.model.unavailability(failures)
            except:
                df.at[index, "IND"] = 0

        self.view_tab_collection[origin] = df
        self.view.output.add_table(title=f"{origin}", view_table=df)

    def view_table(self, view_table: pd.DataFrame):
        """_summary_
        Args:
            view_table (pd.DataFrame): _description_

        Returns:
            view_table: pd.DataFrame
        """
        for col in view_table.columns[3:]:  # iterate over all failure columns
            new_col = " ".join(col.split("_"))

            view_table[new_col] = view_table[col].map(
                self.model.get_element_name, na_action="ignore"
            )
        return view_table

    def calculate_params(
        self,
        *,
        entry: str,
        index: int,
        failures: Iterable,
        group_consumers: int,
        hit_consumers: int,
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

        self.calculate_chi(
            df,
            entry=entry,
            index=index,
            failures=failures,
            hit_consumers=hit_consumers,
            ma=ma,
            mc=mc,
            md=md,
            ta=ta,
            tc=tc,
        )

        self.calculate_dec(
            df,
            entry=entry,
            index=index,
            failures=failures,
            group_consumers=group_consumers,
            hit_consumers=hit_consumers,
            ma=ma,
            mc=mc,
            md=md,
            ta=ta,
            tc=tc,
        )

        self.calculate_fic(
            df,
            entry=entry,
            index=index,
            failures=failures,
            hit_consumers=hit_consumers,
            md=md,
        )

        self.calculate_fec(
            df,
            entry=entry,
            index=index,
            failures=failures,
            group_consumers=group_consumers,
            hit_consumers=hit_consumers,
            md=md,
        )

    def calculate_chi(
        self, df: pd.DataFrame, *, entry: str, index: int, **kwargs: dict
    ):
        df.at[index, "CHI"] = self.model.calculate_chi(**kwargs)
        self.view.output.update_table(self.view.output.tab_collection[entry][1], df)

    def calculate_dec(
        self, df: pd.DataFrame, *, entry: str, index: int, **kwargs: dict
    ):
        df.at[index, "DEC"] = self.model.calculate_dec(**kwargs)
        self.view.output.update_table(self.view.output.tab_collection[entry][1], df)

    def calculate_fic(
        self, df: pd.DataFrame, *, entry: str, index: int, **kwargs: dict
    ):
        df.at[index, "FIC"] = self.model.calculate_fic(**kwargs)
        self.view.output.update_table(self.view.output.tab_collection[entry][1], df)

    def calculate_fec(
        self, df: pd.DataFrame, *, entry: str, index: int, **kwargs: dict
    ):
        df.at[index, "FEC"] = self.model.calculate_fec(**kwargs)
        self.view.output.update_table(self.view.output.tab_collection[entry][1], df)

    def del_tab(self, entry):
        del self.view_tab_collection[entry]

    def separete_failures(self, entry, index, order):
        new_df: pd.DataFrame = self.view_tab_collection[entry].copy()
        self.del_tab(entry)
        ic(new_df)

        new_df.loc[new_df.index > index, "N"] += order - 1
        failure_cols = [col for col in new_df.columns if col.startswith("_FALHA_")]
        new_df = new_df[["SE", "BARRA", "N"] + failure_cols]
        failure_elements_list = new_df.loc[index, failure_cols].to_list()
        for i, failure_element in enumerate(failure_elements_list):
            new_row = {
                "SE": [new_df.at[index, "SE"]],
                "BARRA": [new_df.at[index, "BARRA"]],
                "N": [new_df.at[index, "N"] + i + 1],
                "_FALHA_1": [failure_element],
            }
            new_df = pd.concat(
                [new_df, pd.DataFrame(new_row, index=[0])], ignore_index=True
            )
        # new_df.drop(index, inplace=True)
        new_df.replace(np.nan, None, inplace=True)
        new_df.sort_values("N", axis="index", inplace=True)
        new_df.reset_index(drop=True, inplace=True)
        ic(new_df)
        new_df = self.view_table(new_df)
        for row in new_df.itertuples():
            maxorder = (len(row[1:]) - 3) / 2
            index = row[0]
            failures = self.treat_failures(row[4 : int(4 + maxorder)])[0]
            new_df.at[index, "IND"] = self.model.unavailability(failures)

        self.view_tab_collection[entry] = new_df
        self.view.output.update_table(self.view.output.tab_collection[entry][1], new_df)
        self.view.output
        return

    def get_failure_atts(self, entry, index):
        df: pd.DataFrame = self.view_tab_collection[entry]
        failures_columns = [col for col in df.columns.to_list() if "_FALHA" in col]
        failures = df[failures_columns].iloc[index].to_list()
        failures, order = self.treat_failures(failures)
        if order == 1:
            edge = failures[0]
            return failures, order, self.model.edges[edge][EDGE_TYPE]
        if order == 2:
            edge1 = failures[0]
            edge2 = failures[1]
            return (
                failures,
                order,
                (
                    self.model.edges[edge1][EDGE_TYPE],
                    self.model.edges[edge2][EDGE_TYPE],
                ),
            )

    def treat_failures(self, failures) -> tuple:
        failures = [fail for fail in failures if fail is not None]
        return failures, len(failures)
