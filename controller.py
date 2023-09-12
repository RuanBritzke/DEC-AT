import os

from model import *
from view import View

ALL = 'All'
SE = 'SE'
BUS = 'BUS'

class Controller():
    
    view = None
    
    _buses_or_subs = None

    def __init__(self, model : Model, view : View):
        self.model = model
        self.view = view

        self.view.set_controller(self)
    

    def import_file(self):
            file = self.view.askfilewindow()
            file_ext = os.path.splitext(file)[-1]
            if file_ext != '.PWF':
                self.view.status_bar.set(f'FALHA! Extensão não aceita: "{file_ext}"')
            else:
                self.view.status_bar.set(f'Importando aquivo de: "{file}"')
                buses, lines = self.model.create_net(file)
                self.view.status_bar.set(f'Rede importada: {buses} Barras e {lines} conexões!')
                self.view.ind.enable()
                self.view.dec.enable()

    @property
    def buses_or_subs(self):
        return self._buses_or_subs
    
    def set_buses_or_subs(self, option):
        if option=='0':
            self._buses_or_subs = self.model.load_subs
        elif option=='1':
            self._buses_or_subs = self.model.load_buses
        else:
            self._buses_or_subs = None
            print("wtf from 'set_buses_or_subs'")

    def processingData(self, indexes : list, data : list, sub, buses):
        visited_failures = set()    
        for bus in sorted(buses, key= lambda x: self.model.network.nodes[x][VOLTAGE_LEVEL], reverse=True):
            failureModes = self.model.failure_modes_table(bus)
            for index, failures, _ in failureModes.itertuples():
                if failures in visited_failures: continue
                indexes.append((sub, bus, index))
                data.append([list(failures)])
                visited_failures.add(failures)
        return indexes, data

    def generateFailureTable(self, scope: Literal['ALL', 'SE', 'SUB'], entry: str|int|None = None):
        
        indexes = list()
        data  = list()
        if scope == ALL:
            for kw, buses in self.model.load_subs_dict.items():
                indexes, data = self.processingData(indexes, data, kw, buses)

        elif scope == SE:
            buses = self.model.load_subs_dict[entry]
            indexes, data = self.processingData(indexes, data, entry, buses)

        elif scope == BUS:
            
            sub = self.model.network.nodes[entry][SUB]
            indexes, data = self.processingData(indexes, data, sub, [entry])
        
        mi = pd.MultiIndex.from_tuples(indexes, names= ['SE', 'BARRA', 'N'])
        df = pd.DataFrame(data, index= mi, columns = ['FALHAS'])
        maxFailureLen = df['FALHAS'].apply(len).max()

        for i in range(maxFailureLen):
            df[f'FALHA_{i+1}'] = df['FALHAS'].apply(lambda x: x[i] if len(x) > i else None)
        df.drop(columns='FALHAS', inplace=True)

        flatDf = df.reset_index()
        return flatDf
    
    def computeUnavailabilty(self, entry: str|None = None):
        if entry is None:
            entry = 'Todas SEs'
            table = self.generateFailureTable(scope=ALL)
        elif entry.isalpha():
            table = self.generateFailureTable(scope=SE, entry=entry)
        elif entry.isnumeric():
            table = self.generateFailureTable(scope=BUS, entry=int(entry))

        for row in table.itertuples():
            index, se, bus, n = row[0:4]
            failures = row[4:]
            table.at[index, 'IND'] = self.model.computeUnavailabilty(failures)

        self.view.output.add_table(f'{entry}', table)

