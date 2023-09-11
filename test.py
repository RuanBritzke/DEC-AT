from model import *
from tqdm import tqdm

model = Model()
model.create_net("C:\\Users\\09909909901\\Downloads\\CASO OPERAÇÃO 2023.PWF")
model.max_order = math.inf
results = dict()

indexes = list()
results  = list()
for kw, buses in model.load_subs_dict.items():
    visited_failures = set()
    for bus in sorted(buses, key= lambda x: model.network.nodes[x][VOLTAGE_LEVEL], reverse=True):
        print(f'Calculando {kw} - {bus}', end = '\r')
        paths = model.paths_from_bus_to_sources(bus)
        belongingTable = model.belonging_table(paths = model.paths_from_bus_to_sources(bus))
        failureModes = model.failure_modes_table(belonging_table= belongingTable)
        print( '                       ', end = '\r')
        for index, failures, order in failureModes.itertuples():
            if failures in visited_failures: continue
            indexes.append((kw, bus, index))
            results.append([list(failures), order])
            visited_failures.add(failures)

mi = pd.MultiIndex.from_tuples(indexes, names= ['SE', 'BARRA', 'INDEX'])
test = pd.DataFrame(results, index= mi, columns = ['Falhas', ORDER])
print(test)