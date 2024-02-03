import math
import networkx as nx
import pandas as pd
import struct

pd.options.mode.chained_assignment = None  # default='warn'

from icecream import ic
from typing import Literal, Iterable
from utils.functions import pwf_parser, line_length, power_set
from utils.contants import *
from utils.datatypes import StochasticParams
from collections import defaultdict
from functools import cached_property
from numpy import array, add, prod
from os import PathLike

FR_P = "FR_P"  # Permanent Failure Rate
RP = "RP"  # Repair time of a permanently failed element of the grid
FR_T = "FR_T"  # Temporary Failure Rate
RT = "RT"  # Repair time of a termporaly failed element of the grid
LTT = "LTT"  # Load Transfer Time


def get_tower_type(name):
    return METAL


def get_line_failure_rate_and_repair_time_per_km(
    voltage_level, line_type: str | None = None
):
    if voltage_level == 138:
        return (0.0122, 1.5733)
    if voltage_level == 69:
        return (0.0223, 4.6778)
    if voltage_level == 34.5:
        return (0.0666, 3.6960)
    else:
        return (0, 0)


def get_xfmr_rates_and_times(vp, vs):
    if vp == 138 and vs == 69:
        return (0.0084, 82.31, 0.0194)
    else:
        return (0.0104, 60.41, 0.0137)


class Model(nx.MultiGraph):
    max_order = 2
    path_cutoff_distance = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.DGBT = defaultdict(lambda: 1)

    @classmethod
    def from_pwf(cls, pwf_path: PathLike):
        new_model: Model = cls()
        data = pwf_parser(pwf_path)

        for value in data[DGBT]:
            if value:
                key = value[0]
                voltage = value[1]
                try:
                    voltage = float(voltage)
                except:
                    voltage = 1.0
                new_model.DGBT[key] = voltage

        for bus in data[DBAR]:
            if not bus:
                continue
            (
                cod,
                operation,
                state,
                bus_type,
                base_voltage_level_group,
                name,
                limit_voltage_level_group,
                voltage,
                angle,
                active_power,
                reactive_power,
                minimum_reactive_generation,
                maximum_reactive_generation,
                controlled_bus,
                active_load,
                reactive_load,
                capacitor_reactor,
                area,
                voltage_for_load_definition,
                view_method,
                agg1,
                agg2,
                agg3,
                agg4,
                agg5,
                agg6,
                agg7,
                agg8,
                agg9,
                agg10,
            ) = bus

            if (state == "") or (state == "L"):
                state = ON
            if state == "D":
                state == OFF

            cod = int(cod)
            area = int(area)

            if base_voltage_level_group == "":
                base_voltage_level_group = "0"

            if bus_type == "" or bus_type == "0" or bus_type == "3":
                bus_type = BPQ
            elif bus_type == "1":
                bus_type = BPV
            else:  # bus_type == "2"
                bus_type == REF

            name: str
            name = name.replace("/", "-")
            name = name.replace("_", "-")
            new_model.add_node(
                cod,
                NAME=name,
                SUB=name.split("-")[0],
                VOLTAGE_LEVEL=new_model.DGBT[base_voltage_level_group],
                PG=float(active_power) if active_power != "" else 0,
                QG=float(reactive_power) if reactive_power != "" else 0,
                PL=float(active_load) if active_load != "" else 0,
                QL=float(reactive_load) if reactive_load != "" else 0,
                AREA=area,
                BUS_TYPE=bus_type,
                STATE=state,
            )

        for edge in data[DLIN]:
            (
                origin,
                origin_state,
                operation,
                destiny_state,
                destiny,
                circuit,
                state,
                owner,
                manuverable,
                r,
                x,
                b,
                tap,
                tap_min,
                tap_max,
                phase,
                controlled_bus,
                normal_capacity,
                emergency_capacity,
                tap_number,
                equipament_capacity,
                agg1,
                agg2,
                agg3,
                agg4,
                agg5,
                agg6,
                agg7,
                agg8,
                agg9,
                agg10,
            ) = edge

            if (state == "") or (state == "L"):
                state = NF
            else:
                state = NA

            origin = int(origin)
            destiny = int(destiny)
            circuit = int(circuit)

            if not x:
                x = 0

            if not b:
                b = 0

            if not tap:
                if new_model.nodes[origin][VOLTAGE_LEVEL] > 138:
                    line_type = "LT"
                    name = f"LT {new_model.nodes[origin][NAME]} - {new_model.nodes[origin][NAME]} ({circuit})"
                else:
                    line_type = "LD"
                    name = f"LD {new_model.nodes[origin][NAME]} - {new_model.nodes[destiny][NAME]} ({circuit})"
                weight = line_length(float(x), float(b))
                (
                    temporary_failure_rate,
                    repair_time,
                ) = get_line_failure_rate_and_repair_time_per_km(
                    new_model.nodes[origin][VOLTAGE_LEVEL]
                )

                new_model.add_edge(
                    origin,
                    destiny,
                    key=circuit,
                    weight=weight,
                    NAME=name,
                    STATE=state,
                    PROP=get_tower_type(name),
                    EDGE_TYPE=line_type,
                    FR_P=0,
                    RP=0,
                    FR_T=temporary_failure_rate * weight,
                    REPAIR_TIME=repair_time,
                )
                continue

            hv_lv = sorted(
                [
                    new_model.nodes[origin][VOLTAGE_LEVEL],
                    new_model.nodes[destiny][VOLTAGE_LEVEL],
                ],
                reverse=True,
            )
            voltage = "/".join([str(int(voltage)) for voltage in hv_lv])

            name = f"TR {new_model.nodes[origin][SUB]} {voltage} ({circuit})"
            (
                permanent_failure_rate,
                rp,
                temporary_failure_rate,
            ) = get_xfmr_rates_and_times(*hv_lv)

            new_model.add_edge(
                origin,
                destiny,
                key=circuit,
                weight=0,
                NAME=name,
                STATE=state,
                EDGE_TYPE="TR",
                PROP="{}/{} kV".format(*hv_lv),
                FR_P=permanent_failure_rate,
                RP=rp,
                FR_T=temporary_failure_rate,
                REPAIR_TIME=5,
            )
        return new_model

    def get_element_name(self, element: int | tuple):
        if isinstance(element, int):
            return self.get_node_name(element)
        if isinstance(element, tuple):
            return self.get_edge_name(element)

    def get_node_name(self, barra: int):
        """### Parametros:
            self -> modelo\n
            barra -> número da barra
        ###  Retorna:
            nome da barra
        """
        return self.nodes[barra][NAME]

    def get_edge_name(self, conexao: tuple):
        """### Parametros:
            self -> model\n
            conexao -> a conexao entre duas barras
        ### Retorna:
            nome da conexao (transformador, linha)
        """
        return self.edges[conexao][NAME]

    def get_edge_type(self, edge):
        return self.edges[edge][EDGE_TYPE]

    @cached_property
    def source_buses(self):
        sources = list()
        for bus in self.nodes:
            if (
                self.nodes[bus][VOLTAGE_LEVEL] < 69
                or self.nodes[bus][VOLTAGE_LEVEL] > 138
            ):  # todas as barras com tensão menor que 69kV ou maior que 138kV não são consideradas.
                continue
            for neighbor in self[bus]:
                if self.nodes[neighbor][VOLTAGE_LEVEL] >= 230:
                    sources.append(bus)
        return sorted(sources)

    @cached_property
    def load_buses(self):
        buses = list()
        for bus in self.nodes:
            if self.nodes[bus][BUS_TYPE] not in PQ:
                continue
            if self.nodes[bus][VOLTAGE_LEVEL] > 138:
                continue
            if self.nodes[bus]["PL"] > 0:
                buses.append(bus)
        return buses

    @cached_property
    def load_subs_dict(self):
        """Returns the dictionary with load substations as keys and load bus numbers as values."""
        subs_dict = defaultdict(set)
        for k, v in self.nodes.items():
            for value in self.load_buses:
                if str(k) not in value:
                    continue
                subs_dict[v[SUB]].add(k)
        return subs_dict

    @property
    def load_subs(self):
        return [key for key in self.load_subs_dict.keys()]

    def get_load_buses_from_sub(self, sub: str):
        return list(self.v[sub])

    def get_bus_name(self, bus):
        return self.nodes[bus][NAME]

    def path_weight(
        self, path, weight="weight", consider_state: Literal["y", "n"] = "y"
    ):
        if len(path) == 1:
            return 0
        if consider_state == "n":
            return sum([self.edges[edge][weight] for edge in path])
        else:  # y
            return sum(
                [
                    (
                        self.edges[edge][weight]
                        if self.edges[edge]["STATE"] == NF
                        else self.path_cutoff_distance
                    )
                    for edge in path
                ]
            )

    def get_shortest_path(self, paths: list):
        min_weight = math.inf
        shortest_path = None
        for path in paths:
            current_path_weight = self.path_weight(path)
            if current_path_weight < min_weight:
                min_weight = current_path_weight
                shortest_path = path
        return shortest_path

    def _get_closest_target_from(self, paths):
        longestEdgePaths = list()
        for source in {path[-1][1] for path in paths}:
            sorted_paths = list()
            for path in paths:
                sorted_paths.append(path) if path[-1][1] == source else None
            longestEdgePaths.append(self.get_shortest_path(sorted_paths))
        return [
            path[-1][1]
            for path in sorted(longestEdgePaths, key=lambda x: self._path_weight(x))[:3]
        ]

    def get_filtered_paths_by_targets(self, paths, targets: list) -> list:
        filtered_paths = list()
        for path in paths:
            if path[-1][1] in targets:
                filtered_paths.append(path)
            else:
                continue
        return sorted(filtered_paths, key=lambda path: self._path_weight(path))

    def all_simple_edge_paths(
        self, bus, consider_state: Literal["y", "n"] = "y", *, targets: Iterable = None
    ):
        if bus not in self:
            raise nx.NodeNotFound("Node %s not in graph" % bus)
        if bus in self.source_buses:
            return []
        if targets is None:
            targets = self.source_buses

        visited = [bus]
        stack = [iter(self.edges(bus, keys=True))]
        while stack:
            children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                visited.pop()
            elif (
                self.path_weight(visited[1:], consider_state=consider_state)
                < self.path_cutoff_distance
            ):
                if child[1] in targets:
                    yield visited[1:] + [child]
                elif child[1] not in [v[0] for v in visited[1:]]:
                    visited.append(child)
                    stack.append(iter(self.edges(child[1], keys=True)))
            else:  # self._path_weight() >= self.pathCutOff:
                for u, v, k in [child] + list(children):
                    if v in targets:
                        yield visited[1:] + [(u, v, k)]
                stack.pop()
                visited.pop()

    def add_nodes_to_path_lists(self, paths):
        new_paths = []
        new_path = []
        for path in paths:
            for edge in path:
                new_path = new_path + [(edge[0]), (edge)]
            new_path = new_path + [(path[-1][1])]
            new_paths.append(new_path)
            new_path = []
        return new_paths

    def belonging_table(
        self,
        bus: int | None = None,
        *,
        paths: list | None = None,
        consider_state: Literal["y", "n"] = "y",
        targets: Iterable = None,
    ) -> pd.DataFrame:
        if bus is None and paths is None:
            raise ValueError("Bus and Paths can't be None at the same time!")
        if paths is None:
            paths = self.add_nodes_to_path_lists(
                self.all_simple_edge_paths(
                    bus, consider_state=consider_state, targets=targets
                )
            )

        columns = list()
        truth_table = []

        for path in paths:
            for edge in path:
                if edge not in columns:
                    columns.append(edge)

            row = [column in path for column in columns]
            truth_table.append(row)
        df = pd.DataFrame(truth_table, columns=columns).fillna(value=False)
        return df

    def failure_modes_table(
        self,
        bus=None,
        *,
        consider_state: Literal["y", "n"] = "y",
        belonging_table: pd.DataFrame = None,
        targets: Iterable = None,
    ):
        if belonging_table is None and bus is None:
            raise ValueError(
                "Both 'bus' and 'belonging_table' can't be None at the same time"
            )
        if belonging_table is None:
            belonging_table = self.belonging_table(
                bus, consider_state=consider_state, targets=targets
            )
        failures = pd.DataFrame(columns=[FAILURE, ORDER])
        index = 0
        seen = defaultdict(set)
        for columns in power_set(belonging_table.columns, max_size=self.max_order):
            order = len(columns)
            last_order = order - 1
            seen[order] = seen[order].union(seen[last_order])

            if set(columns).intersection(seen[last_order]) or order == 0:
                continue

            arrays = array(belonging_table[list(columns)])
            if add.reduce(arrays, axis=1).all():
                failures.loc[index] = [columns, len(columns)]
                index += 1
                seen[order] = seen[order].union(columns)

            # if len(seen[order]) == len(belonging_table.columns):
            #     break

        return failures

    def get_element_stochastic_param(
        self, element: tuple | int, param: Literal["FR_P", "FR_T", "RP", "RT"]
    ):
        if isinstance(element, int):  # element is a bus
            if hasattr(self, "bus_data"):
                if element in self.bus_data:
                    return self.bus_data[element][param]
            return self.nodes[element][param]
        if hasattr(self, "edge_data"):
            if element in self.edge_data:
                return self.edge_data[element][param]
            u, v, k = element
            if (v, u, k) in self.edge_data:
                return self.edge_data[(v, u, k)][param]
        return self.edges[element][param]

    def get_element_stochastic_params(
        self, failures: Iterable[int | tuple]
    ) -> list[StochasticParams]:
        stochastic_params_list = list()
        for failure in failures:
            stochastic_params = StochasticParams(
                self.get_element_stochastic_param(failure, FR_P),
                self.get_element_stochastic_param(failure, RP),
                self.get_element_stochastic_param(failure, FR_T),
                self.get_element_stochastic_param(failure, RT),
            )
            stochastic_params_list.extend(stochastic_params)
        return stochastic_params_list

    def unavailability(self, failures) -> float:
        ic(failures)
        if len(failures) == 1:
            frp, rp, frt, rt = ic(self.get_element_stochastic_params(failures))
            return ic(self.unavailability_p(frp, rp) + self.unavailability_t(frt, rt))
        frp1, rp1, frt1, rt1, frp2, rp2, frt2, rt2 = ic(
            self.get_element_stochastic_params(failures)
        )
        return ic(
            self.overlaping_unavailabilty_pp((frp1, rp1), (frp2, rp2))
            + self.overlaping_unavailabilty_pt(
                (frp1, frt1, rp1, rt1), (frp2, frt2, rp2, rt2)
            )
        )

    def unavailability_p(self, permanent_failure_rate, repair_time) -> float:
        return permanent_failure_rate * repair_time

    def unavailability_t(self, temporary_failure_rate, repair_time) -> float:
        return temporary_failure_rate * repair_time

    def overlaping_unavailabilty_pp(
        self, failure_1_params: tuple, failure_2_params: tuple
    ) -> float:
        frp1, rp1 = failure_1_params
        frp2, rp2 = failure_2_params
        return frp1 * rp1 * frp2 * rp2 / 8760

    def overlaping_unavailabilty_pt(
        self, failure_1_params: tuple, failure_2_params: tuple
    ) -> float:
        frp1, frt1, rp1, rt1 = failure_1_params
        frp2, frt2, rp2, rt2 = failure_2_params

        return (frp1 * rp1 * frt2 * rt2 + frp2 * rp2 * frt1 * rt1) / 8760

    def calculate_dec(
        self,
        *,
        group_consumers: int,
        hit_consumers: int,
        failures: Iterable,
        ma: float = 0,
        mc: float = 0,
        md: float = 0,
        ta: float = 0,
        tc: float = 0,
        **kwargs,
    ) -> float:
        ic(failures)
        if len(failures) == 1:  # falhas de primeira ordem
            failure = failures[0]
            frp = self.get_element_stochastic_param(failure, FR_P)
            frt = self.get_element_stochastic_param(failure, FR_T)
            rp = self.get_element_stochastic_param(failure, RP)
            rt = self.get_element_stochastic_param(failure, RT)

            Up = (
                frp * rp * (1 - md)
            )  # valor base para falhas permanentes com transferencias automáticas
            Ut = (
                frt * rt * (1 - md)
            )  # valor base para falhas temporárias com transferencias automáticas

            if ta < rp:
                Upa = -(frp * rp * ma) + (
                    frp * ma * ta
                )  # reudução da indisponibilidade da falha permanente
                Up += Upa  # pela trasnferencia manual MT

            if ta < rt:
                Uta = -(frt * rt * ma) + (
                    frt * ma * ta
                )  # reudução da indisponibilidade falha permanente
                Ut += Uta  # pela transferencia manual MT

            if tc < rp:
                Upc = -(frp * rp * mc) + (
                    frp * mc * tc
                )  # reudução dc indisponibilidcde dc fclhc permcnente
                Up += Upc  # pelc trcsnferencic mcnucl MT

            if tc < rt:
                Utc = -(frt * rt * mc) + (
                    frt * mc * tc
                )  # reudução dc indisponibilidcde fclhc permcnente
                Ut += Utc

            return hit_consumers * (Up + Ut) / group_consumers
        if len(failures) == 2:
            frp1, rp1, frt1, rt1, frp2, rp2, frt2, rt2 = (
                self.get_element_stochastic_params(failures)
            )

            Upp = self.overlaping_unavailabilty_pp((frp1, rp1), (frp2, rp2)) * (1 - md)

            if ta < rp1 and ta < rp2:
                Uppa = (
                    -(frp1 * frp2 * rp1 * rp2 * ma) + (frp1 * frp2 * ma * ta)
                ) / 8760  # reudução da indisponibilidade da falha permanente
                Upp += Uppa  # pela trasnferencia manual MT

            if tc < rp1 and tc < rp2:
                Uppc = (
                    -(frp1 * frp2 * rp1 * rp2 * mc) + (frp1 * frp2 * mc * tc)
                ) / 8760  # reudução dc indisponibilidcde dc fclhc permcnente
                Upp += Uppc  # pelc trcsnferencic manual MT

            Upt = (
                ((frp1 * rp1 * frt2 * rt2) + (frp2 * rp2 * frt1 * rt1))
                * (1 - md)
                / 8760
            )
            # a redução para falhas
            # permantnentes e temporaias
            # combinadas
            # não é facilmente obtida,
            # pois existem dois tempos de
            # reparo diferntes.
            ic(Upp, Upt)
            return (Upp + Upt) * hit_consumers / group_consumers
        return 0

    def calculate_fec(
        self,
        *,
        failures: Iterable,
        hit_consumers: int,
        group_consumers: int,
        md: float = 0,
        **kwargs,
    ):
        if len(failures) == 1:
            failure = failures[0]
            frp = self.get_element_stochastic_param(failure, FR_P)
            frt = self.get_element_stochastic_param(failure, FR_T)
            return hit_consumers * (frp + frt) * (1 - md) / group_consumers
        if len(failures) == 2:
            frp1, rp1, frt1, rt1, frp2, rp2, frt2, rt2 = (
                self.get_element_stochastic_params(failures)
            )
            fr_pp = frp1 * frp2 * (rp1 + rp2) * (1 - md) / 8760
            fr_pt = (frt1 * frp2 * (rt1 + rp2) + frp1 * frt2 * (rp1 + rt2)) / 8760
            return hit_consumers * (fr_pp + fr_pt) / group_consumers

    def calculate_ens(self, *, dec, avg_load, max_load, **kwargs):
        return dec * avg_load, dec * max_load
