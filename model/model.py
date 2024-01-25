import math
import networkx as nx
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('future.no_silent_downcasting', True)

from io import StringIO
from typing import Literal, Iterable
from utils.functions import pwf_parser, line_length, power_set
from utils.contants import *
from collections import defaultdict
from functools import cached_property
from numpy import array, add, prod
from os import PathLike


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
    max_order = 3
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
                    name = f"LT {origin} - {destiny} ({circuit})"
                else:
                    line_type = "LD"
                    name = f"LD {origin} - {destiny} ({circuit})"
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
                    PERMANENT_FAILURE_RATE=0,
                    REPLACEMENT_TIME=0,
                    TEMPORARY_FAILURE_RATE=temporary_failure_rate * weight,
                    REPAIR_TIME=repair_time,
                )
                continue

            name = f"TR {new_model.nodes[destiny][NAME]} - ({new_model.nodes[destiny][NAME]}) ({circuit})"
            hv_lv = sorted(
                [
                    new_model.nodes[origin][VOLTAGE_LEVEL],
                    new_model.nodes[destiny][VOLTAGE_LEVEL],
                ],
                reverse=True,
            )
            (
                permanent_failure_rate,
                replacement_time,
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
                PERMANENT_FAILURE_RATE=permanent_failure_rate,
                REPLACEMENT_TIME=replacement_time,
                TEMPORARY_FAILURE_RATE=temporary_failure_rate,
                REPAIR_TIME=5,
            )
        return new_model

    def get_edge_name(self, edge):
        """### Parametros:
            self -> model\n
            edge -> a ligação entre duas barras
        ### Retorna:
            tipo da ligação (transformador, linha)
        """
        return self.edges[edge][NAME]

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

    def path_weight(self, path, weight="weight"):
        if len(path) == 1:
            return 0
        return sum([self.edges[edge][weight] for edge in path[1:]])

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

    def all_simple_edge_paths(self, bus):
        if bus not in self:
            raise nx.NodeNotFound("Source node %s not in graph" % bus)
        if bus in self.source_buses:
            return []

        # é possível calcular a distancia maxima dependendo da carga da barra, e impedancia da linha:
        # interessante para não ser necessário o estudo do fluxo de potência.

        visited = [bus]
        stack = [iter(self.edges(bus, keys=True))]

        while stack:
            children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                visited.pop()
            elif self.path_weight(visited[1:]) < self.path_cutoff_distance:
                if child[1] in self.source_buses:
                    yield visited[1:] + [child]
                elif child[1] not in [v[0] for v in visited[1:]]:
                    visited.append(child)
                    stack.append(iter(self.edges(child[1], keys=True)))
            else:  # self._path_weight() >= self.pathCutOff:
                for u, v, k in [child] + list(children):
                    if v in self.source_buses:
                        yield visited[1:] + [(u, v, k)]
                stack.pop()
                visited.pop()

    def path_with_nodes(self, path : list):
        new_path = list()
        for u, v, j in path:
            new_path.extend([u, (u, v, j)])        
        return new_path

    def belonging_table(
        self, bus: int | None = None, *, paths: list | None = None
    ) -> pd.DataFrame:
        if bus is None and paths is None:
            raise ValueError("Bus and Paths can't be None at the same time!")
        if paths is None:
            paths = self.all_simple_edge_paths(bus)

        columns = list()
        truth_table = []

        for path in paths:
            path = self.path_with_nodes(path)
            for edge in path:
                if edge not in columns:
                    columns.append(edge)

            row = [column in path for column in columns]
            truth_table.append(row)
        df = pd.DataFrame(truth_table, columns=columns).fillna(value=False)
        return df

    def failure_modes_table(self, bus=None, *, belonging_table: pd.DataFrame = None):
        if belonging_table is None and bus is None:
            raise ValueError(
                "Both 'bus' and 'belonging_table' can't be None at the same time"
            )
        if belonging_table is None:
            belonging_table = self.belonging_table(bus)

        failures = pd.DataFrame(columns=[FAILURE, ORDER])
        index = 0
        seen = defaultdict(set)
        for columns in power_set(belonging_table.columns, max_size=self.max_order):
            order = len(columns)
            last_order = order - 1
            seen[order] = seen[order].union(seen[last_order])

            if order == 0 or set(columns).intersection(seen[last_order]):
                continue

            arrays = array(belonging_table[list(columns)])
            if add.reduce(arrays, axis=1).all():
                failures.loc[index] = [columns, len(columns)]
                index += 1
                seen[order] = seen[order].union(columns)
            if len(seen[order]) == len(belonging_table.columns):
                break

        return failures

    def time_and_probabilistic_params_per_failure(self, failures: Iterable) -> tuple:
        if len(failures) == 1:
            failure = failures[0]
            return (
                self.edges[failure][PERMANENT_FAILURE_RATE],
                self.edges[failure][TEMPORARY_FAILURE_RATE],
                self.edges[failure][REPLACEMENT_TIME],
                self.edges[failure][REPAIR_TIME],
            )

        elif len(failures) == 2:  # len(failures) == 2:
            failure_1 = failures[0]
            failure_2 = failures[1]

            permanent_failure_rate_1 = self.edges[failure_1][PERMANENT_FAILURE_RATE]
            permanent_failure_rate_2 = self.edges[failure_2][PERMANENT_FAILURE_RATE]

            temporary_failure_rate_1 = self.edges[failure_1][TEMPORARY_FAILURE_RATE]
            temporary_failure_rate_2 = self.edges[failure_2][TEMPORARY_FAILURE_RATE]

            replacement_time_1 = self.edges[failure_1][REPLACEMENT_TIME]
            repair_time_1 = self.edges[failure_1][REPAIR_TIME]

            replacement_time_2 = self.edges[failure_2][REPLACEMENT_TIME]
            repair_time_2 = self.edges[failure_2][REPAIR_TIME]

            return (
                permanent_failure_rate_1,
                temporary_failure_rate_1,
                replacement_time_1,
                repair_time_1,
                permanent_failure_rate_2,
                temporary_failure_rate_2,
                replacement_time_2,
                repair_time_2,
            )
        else:
            return

    def adjusted_unavailability(
        self,
        *,
        failures: Iterable,
        beta=1,
        ma: float = 0,
        mc: float = 0,
        md: float = 0,
        ta: float = 0,
        tc: float = 0,
    ):
        order = len(failures)

        if order == 1:
            (
                permanent_failure_rate,
                temporary_failure_rate,
                replacement_time,
                repair_time,
            ) = self.time_and_probabilistic_params_per_failure(failures)
            unavailability_time = (
                beta * permanent_failure_rate * replacement_time
                + beta * temporary_failure_rate * repair_time
            ) * (1 - ma - mc - md) + (
                permanent_failure_rate + temporary_failure_rate
            ) * (
                ta * ma + tc * mc
            )
            return unavailability_time

        elif order == 2:
            (
                permanent_failure_rate_1,
                temporary_failure_rate_1,
                replacement_time_1,
                repair_time_1,
                permanent_failure_rate_2,
                temporary_failure_rate_2,
                replacement_time_2,
                repair_time_2,
            ) = self.time_and_probabilistic_params_per_failure(failures)
            unavailability_time = (
                (
                    beta
                    * permanent_failure_rate_1
                    * temporary_failure_rate_2
                    * replacement_time_1
                    * repair_time_2
                    + beta
                    * permanent_failure_rate_2
                    * temporary_failure_rate_1
                    * replacement_time_2
                    * repair_time_1
                )
                * (1 - ma - mc - md)
                + (permanent_failure_rate_1 * permanent_failure_rate_2)
                * (ma + mc)
                * (ta + tc) ** 2
            ) / 8760
            return unavailability_time

    def unavailability(self, failures: Iterable) -> float:
        return self.adjusted_unavailability(
            failures=failures, beta=1, ma=0, mc=0, md=0, ta=0, tc=0
        )

    def calculate_chi(
        self,
        *,
        hit_consumers: int,
        failures: Iterable,
        beta=1,
        ma: float = 0,
        mc: float = 0,
        md: float = 0,
        ta: float = 0,
        tc: float = 0,
    ):
        return hit_consumers * self.adjusted_unavailability(
            failures=failures, beta=beta, ma=ma, mc=mc, md=md, ta=ta, tc=tc
        )

    def calculate_dec(
        self,
        *,
        group_consumers: int,
        hit_consumers: int,
        failures: Iterable,
        beta=1,
        ma: float = 0,
        mc: float = 0,
        md: float = 0,
        ta: float = 0,
        tc: float = 0,
    ):
        return (
            self.calculate_chi(
                hit_consumers=hit_consumers,
                failures=failures,
                beta=beta,
                ma=ma,
                mc=mc,
                md=md,
                ta=ta,
                tc=tc,
            )
            / group_consumers
        )

    def calculate_fic(self, *, hit_consumers: int, failures: Iterable, md: float = 0):
        order = len(failures)
        if order == 1:
            (
                permanent_failure_rate,
                temporary_failure_rate,
                _,
                _,
            ) = self.time_and_probabilistic_params_per_failure(failures)
            return (
                hit_consumers
                * (permanent_failure_rate + temporary_failure_rate)
                * (1 - md)
            )
        elif order == 2:
            (
                permanent_failure_rate_1,
                temporary_failure_rate_1,
                repair_time_1,
                replacement_time_1,
                permanent_failure_rate_2,
                temporary_failure_rate_2,
                repair_time_2,
                replacement_time_2,
            ) = self.time_and_probabilistic_params_per_failure(failures)
            return (
                hit_consumers
                * (
                    permanent_failure_rate_1
                    * temporary_failure_rate_2
                    * (replacement_time_1 + repair_time_2)
                    + permanent_failure_rate_2
                    * temporary_failure_rate_1
                    * (repair_time_1 + replacement_time_2)
                )
                * (1 - md)
                / 8760
            )

    def calculate_fec(
        self,
        *,
        group_consumers: int,
        hit_consumers: int,
        failures: Iterable,
        md: float,
        **kwargs,
    ):
        return (
            self.calculate_fic(hit_consumers=hit_consumers, failures=failures, md=md)
            / group_consumers
        )
