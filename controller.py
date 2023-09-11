import os

from model import *
from view import *

class Controller():
    
    view = None
    
    _buses_or_subs = None

    def __init__(self, model : Model):
        self.model = model
    
    def set_view(self, view):
        self.view = view

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
            print("wtf?")

    def calculate_unavailabilty(self, scope: str|int):
        if self.view is None:
            return
        if scope == 'All':
            self.view.output.add_table('Indisponibiliades', self.unavailabilty_all())
        return
    
    def unavailabilty_all(self):
        print('Calculating Unavailabitly')
        indexes = list()
        results  = list()
        for kw, buses in self.model.load_subs_dict.items():
            visited_failures = set()
            for bus in sorted(buses, key= lambda x: self.model.network.nodes[x][VOLTAGE_LEVEL], reverse=True):
                paths = self.model.paths_from_bus_to_sources(bus)
                belongingTable = self.model.belonging_table(paths = self.model.paths_from_bus_to_sources(bus))
                failureModes = self.model.failure_modes_table(belonging_table= belongingTable)
                for index, failures, _ in failureModes.itertuples():
                    if failures in visited_failures: continue
                    indexes.append((kw, bus, index))
                    results.append([list(failures)])
                    visited_failures.add(failures)
        mi = pd.MultiIndex.from_tuples(indexes, names= ['SE', 'BARRA', 'nº'])
        df = pd.DataFrame(results, index= mi, columns = ['FALHAS'])
        maxFailureLen = df['FALHAS'].apply(len).max()
        for i in range(maxFailureLen):
            df[f'FALHA_{i+1}'] = df['FALHAS'].apply(lambda x: x[i] if len(x) > i else None)
        df.drop(columns='FALHAS', inplace=True)
        print('Done')  
        return df