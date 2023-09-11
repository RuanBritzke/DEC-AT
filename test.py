from model import *
from tqdm import tqdm

model = Model()
model.create_net("CASO_BASE.PWF")
model.max_order = 2
model.pathCutOff = 200
results = dict()

indexes = list()
results  = list()
kw = 'CPA'
buses = model.load_subs_dict[kw]
visited_failures = set()
pathString = ""

for bus in sorted(buses, key= lambda x: model.network.nodes[x][VOLTAGE_LEVEL], reverse=True):
    paths = model.paths_from_bus_to_sources(bus)
    for path in paths:
        pathString = pathString + ", ".join([str(x) for x in path]) + '\n'
    belongingTable = model.belonging_table(paths = model.paths_from_bus_to_sources(bus))
    print(belongingTable)
    failureModes = model.failure_modes_table(belonging_table= belongingTable)
    for index, failures, _ in failureModes.itertuples():
        if failures in visited_failures: continue
        indexes.append((kw, bus, index))
        results.append([list(failures)])
        visited_failures.add(failures)


with open('paths.txt', 'w') as file:
    file.write(pathString)

mi = pd.MultiIndex.from_tuples(indexes, names= ['SE', 'BARRA', 'INDEX'])
test = pd.DataFrame(results, index= mi, columns = ['FALHAS'])

maxFailureLen = test['FALHAS'].apply(len).max()

for i in range(maxFailureLen):
    test[f'FALHA_{i+1}'] = test['FALHAS'].apply(lambda x: x[i] if len(x) > i else None)

test.drop(columns='FALHAS', inplace=True)


print(test)
