import pathlib as pl
import math
import networkx as nx
import os
import pandas as pd
import signal

pd.options.mode.chained_assignment = None  # default='warn'

from contextlib import contextmanager
from io import StringIO
from typing import Literal, Iterable, Optional
from collections import defaultdict
from itertools import combinations
from functools import cached_property
from numpy import array, add, prod

OFF: Literal = 'D'
PV: Literal = 'PV'
LOAD: Literal = 'LOAD'
VOLTAGE_LEVEL: Literal = 'VOLTAGE_LEVEL'
SUB: Literal = 'SUB'
NAME: Literal = 'NAME'
AREA: Literal = 'AREA'
BUS_TYPE: Literal = 'BUS_TYPE'
EDGE_TYPE: Literal = 'EDGE_TYPE'
LD: Literal = 'LD'
TRAFO: Literal = 'TRAFO'
TEMPORARY_FAILURE_RATE: Literal = "TEMPORARY_FAILURE_RATE"
PERMANENT_FAILURE_RATE: Literal = "PERMANENT_FAILURE_RATE"
REPLACEMENT_TIME: Literal = "REPLACEMENT_TIME"
REPAIR_TIME: Literal = "REPAIR_TIME"
LOAD_TRANSFER_TIME: float = 1.5
LOAD_TRANSFER: Literal = 0
FAILURE: Literal = "Failure"
PROP: Literal = "Característica"
ORDER: Literal = 'Order'
UT: Literal = 'Unavailability'
Times = tuple[float, float]
FailureRates = tuple[float, float]
Unavailability = tuple[FailureRates, Times]

SAIDI: Literal = 'SAIDI'

def PU():
    return 1

def power_set(entities, max_size=math.inf):
    n = min(len(entities), max_size)
    for i in range(1, n+1):
        yield from combinations(entities, r=i)


def line_length(X, B):
    if math.isnan(X) or math.isnan(B):
        return 0
    # returns the aproximate legnth of the line in km
    return 7.8*math.sqrt(X*B)


def extract_from_pwf(file_path: os.PathLike, target: Literal["DBAR", "DLIN", "DBGT"]):
    if target == 'DBAR':
        header = target
        colspecs = [
            (0, 5), (5, 6), (6, 7), (7, 8), (8, 10), (10, 22), (58, 63), (73, 76)]
    elif target == "DLIN":
        header = target
        colspecs = [
            (0, 5),  (10, 15), (15, 17), (17, 18), (18, 19), (19, 20), (20, 26), (26, 32), (32, 38), (38, 43)]
    elif target == "DGBT":
        header = target
        colspecs = [
            (0, 2), (2, 8)
        ]

    with open(file_path, 'r') as reader:
        lines = reader.readlines()

    start = end = None
    flag = False
    for index, line in enumerate(lines):
        if header in line:
            start = index + 1
            flag = True
        if '99999' in line[0:6] and flag:
            end = index
            break

    string = ""
    if not start or not end:
        return pd.DataFrame()  # empty dataframe
    for line in lines[start:end]:
        for i, e in colspecs:
            string = string + line[i: e].strip() + ","
        string = string + '\n'

    csv_string = StringIO(string)

    df = pd.read_csv(csv_string)
    df = df.dropna(axis=1, how='all')
    return df


def create_line(network: nx.MultiGraph, frm, to, circuit, x, mvar):
    ori, des = sorted([frm, to])
    voltage_level = network.nodes[frm][VOLTAGE_LEVEL]
    name = f'Linha CA {ori} ({network.nodes[ori][NAME]}) - {des} ({network.nodes[des][NAME]}) - {circuit}'
    edge_type = LD
    length = line_length(x, mvar)
    permanent_failure_rate = 0
    replacement_time = 0

    if voltage_level == 138:
        temporary_failure_rate = length*0.0122
        repair_time = 1.5733
    elif voltage_level == 69:
        temporary_failure_rate = length*0.0223
        repair_time = 4.6778
    elif voltage_level == 34.5:
        temporary_failure_rate = length*0.0666
        repair_time = 3.6960
    else:
        temporary_failure_rate = 0
        repair_time = 0

    network.add_edge(
        frm,
        to,
        key=int(circuit),
        NAME=name,
        PROP=f'Metálica + {voltage_level}',
        EDGE_TYPE=edge_type,
        weight=length,
        PERMANENT_FAILURE_RATE=permanent_failure_rate,
        REPLACEMENT_TIME=replacement_time,
        TEMPORARY_FAILURE_RATE=temporary_failure_rate,
        REPAIR_TIME=repair_time,
    )


def create_trafo(network: nx.MultiGraph, frm, to, circuit):
    ori, des = sorted(
        [frm, to], key=lambda x: network.nodes[x][VOLTAGE_LEVEL], reverse=True)
    hv = network.nodes[ori][VOLTAGE_LEVEL]
    lv = network.nodes[des][VOLTAGE_LEVEL]
    edge_type = TRAFO
    length = 0
    name = f'Transformador ({network.nodes[ori][NAME]}) - ({network.nodes[des][NAME]}) - {circuit}'
    repair_time = 5

    if hv == 138 and lv == 69:
        permanent_failure_rate = 0.0084
        replacement_time = 82.31
        temporary_failure_rate = 0.0194

    else:
        permanent_failure_rate = 0.0104
        replacement_time = 60.41
        temporary_failure_rate = 0.0137

    network.add_edge(
        frm,
        to,
        key=int(circuit),
        NAME=name,
        PROP= f"{hv}/{lv} kV",
        EDGE_TYPE=edge_type,
        weight=length,
        PERMANENT_FAILURE_RATE=permanent_failure_rate,
        REPLACEMENT_TIME=replacement_time,
        TEMPORARY_FAILURE_RATE=temporary_failure_rate,
        REPAIR_TIME=repair_time,
    )


class Model:

    network = nx.MultiGraph()

    DGBT = defaultdict(PU)

    max_order = 2
    pathCutOff = 200

    observer = None

    def set_observer(self, obs):
        self.observer = obs

    def create_net(self, pwf):

        self.network = nx.MultiGraph()
        bars = extract_from_pwf(pwf, 'DBAR')
        conection = extract_from_pwf(pwf, 'DLIN')
        df = extract_from_pwf(pwf, 'DGBT')
        self.DGBT = df.set_index(df[df.columns[0]]).to_dict()[
            '( kV)'] if not df.empty else self.DGBT

        for _, NUM, E, T, Gb, name, Pl, Are in bars.itertuples():
            if E == OFF:
                continue
            Vn = '0' if isinstance(Gb, float) else Gb
            if NUM == 2290: 
                name = 'SAI-34.5'
            self.network.add_node(
                NUM,
                NAME=name,
                SUB=name.split("-")[0],
                VOLTAGE_LEVEL=self.DGBT[Vn],
                AREA=Are,
                BUS_TYPE=PV if pd.isna(Pl) else LOAD)

        for _, frm, to, circuit, state, _, _, x, mvar, Tap in conection.itertuples():
            if state == OFF:
                continue
            if math.isnan(Tap):
                create_line(self.network, frm, to, circuit, x, mvar)
            else:  # Tap
                create_trafo(self.network, frm, to, circuit)
        
        return (len(self.network.nodes), len(self.network.edges))

    def get_edge_name(self, edge):
        return self.network.edges[edge][NAME]
            
    @cached_property
    def source_buses(self):
        sources = set()
        for bus in self.network.nodes:
            if self.network.nodes[bus][VOLTAGE_LEVEL] < 69  or  self.network.nodes[bus][VOLTAGE_LEVEL] > 138: # todas as barras com tensão menor que 69kV ou maior que 138kV não são consideradas.
                continue
            for neighbor in self.network[bus]:
                if self.network.nodes[neighbor][VOLTAGE_LEVEL] >= 230:
                    sources.add(bus)
        return sorted(list(sources))

    @cached_property
    def load_buses(self):
        buses = list()
        for bus in self.network.nodes:
            if self.network.nodes[bus][AREA] > 8:
                continue
            if self.network.nodes[bus][BUS_TYPE] != LOAD:
                continue
            if self.network.nodes[bus][VOLTAGE_LEVEL] > 138:
                continue
            if any([True for neighbor in self.network[bus] if self.network.nodes[neighbor][VOLTAGE_LEVEL] > 138]):
                continue
            buses.append(bus)
        return sorted(buses)

    @cached_property
    def load_subs_dict(self):
        """Returns the dictionary with load substations as keys and load bus numbers as values.
        """
        subs_dict = defaultdict(set)
        for k, v in self.network.nodes.items():
            if k not in self.load_buses:
                continue
            subs_dict[v[SUB]].add(k)
        return subs_dict

    @property
    def load_subs(self):
        return [key for key in self.load_subs_dict.keys()]

    def get_load_buses_from_sub(self, sub: str):
        return list(self.v[sub])


    def get_bus_name(self, bus):
        return self.network.nodes[bus][NAME]

    def path_weight(self, path, weight='weight'):
        if len(path) == 1:
            return 0
        return sum([self.network.edges[edge][weight] for edge in path[1:]])
    
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
        return [path[-1][1] for path in sorted(longestEdgePaths, key=lambda x: self._path_weight(x))[:3]]

    def get_filtered_paths_by_targets(self, paths, targets: list) -> list:
        filtered_paths = list()
        for path in paths:
            if path[-1][1] in targets:
                filtered_paths.append(path)
            else:
                continue
        return sorted(filtered_paths, key=lambda path: self._path_weight(path))

    def paths_from_bus_to_sources(self, bus):
        if bus not in self.network:
            raise nx.NodeNotFound("Source node %s not in graph" % bus)
        if bus in self.source_buses:
            return []

        visited = [bus]
        stack = [iter(self.network.edges(bus, keys=True))]

        while stack:
            children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                visited.pop()
            elif self.path_weight(visited[1:]) < self.pathCutOff:
                if child[1] in self.source_buses:
                    yield visited[1:] + [child]
                elif child[1] not in [v[0] for v in visited [1:]]:
                    visited.append(child)
                    stack.append(iter(self.network.edges(child[1], keys= True)))
            else: # self._path_weight() >= self.pathCutOff:
                for u, v, k in [child] + list(children):
                    if v in self.source_buses:
                        yield visited[1:] + [(u, v, k)]
                stack.pop()
                visited.pop()

    def belonging_table(self, bus: int | None = None,*, paths: list | None = None) -> pd.DataFrame:
        if bus is None and paths is None:
            raise ValueError("Bus and Paths can't be None at the same time!")
        if paths is None:
            paths = self.paths_from_bus_to_sources(bus)

        columns = list()
        truth_table = []

        for path in paths:
            for edge in path:
                if edge not in columns: columns.append(edge)

            row = [column in path for column in columns]
            truth_table.append(row)
        df = pd.DataFrame(truth_table, columns=columns).fillna(value = False)
        return df

    def failure_modes_table(self, bus=None, *, belonging_table: pd.DataFrame = None):
        if belonging_table is None and bus is None:
            raise ValueError(
                "Both 'bus' and 'belonging_table' can't be None at the same time")
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

    def computeUnavailabiltyValues(self, failures : Iterable) -> tuple[FailureRates, Times]:
        failures = [fail for fail in failures if fail is not None]
        order = len(failures)
        
        permanent_failure_rate = prod([self.network.edges[fail][PERMANENT_FAILURE_RATE] for fail in failures])
        temporary_failure_rate = prod([self.network.edges[fail][TEMPORARY_FAILURE_RATE] for fail in failures])
        replacement_time =       prod([self.network.edges[fail][REPLACEMENT_TIME] for fail in failures])
        repair_time =            prod([self.network.edges[fail][REPAIR_TIME] for fail in failures])  

        failure_rates = (permanent_failure_rate, temporary_failure_rate)
        repair_times = (replacement_time, repair_time)

        unavailability = ((permanent_failure_rate*replacement_time + temporary_failure_rate+repair_time) + (permanent_failure_rate*temporary_failure_rate))/(8760**(order-1))

        return (unavailability, failure_rates, repair_times)

    def unavailabilty(self, failures) -> float:
        return self.computeUnavailabiltyValues(failures)[0]

    def compute_saidi(
            self,
            failure: Iterable,
            *,
            beta=1,
            ma: float = 0,
            mc: float = 0,
            md: float = 0,
            ta: float = 0,
            tc: float = 0):
        
        (_, (permanent_failure_rate, temporary_failure_rate), (replacement_time,repair_time)) = self.unavailability(failure)
        replacement = beta*permanent_failure_rate*replacement_time
        rapair = beta*temporary_failure_rate*repair_time        
        rates = permanent_failure_rate + temporary_failure_rate

        ut = ((replacement + rapair)*(1 - ma - mc - md) + (rates)*(ta*ma + tc*mc))
        return ut