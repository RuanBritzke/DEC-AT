"""Este módulo contem todas as strings, e discionários constantes que serão usadas pelo programa"""

from collections import namedtuple


# General Literals
ON = 1
OFF = 0
PQ0 = "0"
PV = "1"
V = "2"
PQ3 = "3"
PQ = [PQ0, PQ3]
BPV = "1"
BPQ = "0"
REF = "2"
VOLTAGE_LEVEL = "VOLTAGE_LEVEL"
SUB = "SUB"
BUS = "BUS"
NAME = "NAME"
AREA = "AREA"
BUS_TYPE = "BUS_TYPE"
EDGE_TYPE = "EDGE_TYPE"
REPLACEMENT_TIME = "REPLACEMENT_TIME"
REPAIR_TIME = "REPAIR_TIME"
LOAD_TRANSFER_TIME = 1.5
LOAD_TRANSFER = 0
FAILURE = "Failure"
PROP = "Característica"
ORDER = "Order"
UT = "Unavailability"
XFMR = "XFMR"
METAL = "Metalica"

NF = "NF"
NA = "NA"
# Model Literals
TEMPORARY_FAILURE_RATE = "TEMPORARY_FAILURE_RATE"
PERMANENT_FAILURE_RATE = "PERMANENT_FAILURE_RATE"

# Control Literals

# View Literals

# PWF Literals
EXEEND = "99999"
END = "END"
DARE = "DARE"
DBAR = "DBAR"
DGBT = "DGBT"
DLIN = "DLIN"

# CODE FIELDS
DARE_FIELDS = namedtuple(
    "DARE_FIELDS",
    [
        "Numero",
        "Blank_1",
        "Intercambio_Liquido",
        "Blank_2",
        "Nome",
        "Blank_3",
        "Intercambio_Minimo",
        "Blank_4",
        "Intercambio_Maximo",
    ],
)
DBAR_FIELDS = namedtuple(
    "DBAR_FIELDS",
    [
        "Numero",
        "Operacao",
        "Estado",
        "Tipo",
        "Grupo_de_Base_de_Tensao",
        "Nome",
        "Grupo_de_Limite_de_Tensao",
        "Tensao",
        "Angulo",
        "Geracao_Ativa",
        "Geracao_Reativa",
        "Geracao_Reativa_Minima",
        "Geracao_Reativa_Maxima",
        "Barra_Controlada",
        "Carga_Ativa",
        "Carga_Reativa",
        "Capacitor_Reator",
        "Area",
        "Tensao_para_Definicao_de_Carga",
        "Modo_de_Visualizacao",
        "Agregador_1",
        "Agregador_2",
        "Agregador_3",
        "Agregador_4",
        "Agregador_5",
        "Agregador_6",
        "Agregador_7",
        "Agregador_8",
        "Agregador_9",
        "Agregador_10",
    ],
)
DGBT_FIELDS = namedtuple("DGBT_FIELDS", ["Grupo", "Tensao"], defaults=(0, 1.0))

DLIN_FIELDS = namedtuple(
    "DLIN_FIELDS",
    [
        "Da_Barra",
        "Abertura_Da_Barra",
        "Blank_1",
        "Operacao",
        "Blank_2",
        "Abertura_Para_Barra",
        "Para_Barra",
        "Circuito",
        "Estado",
        "Proprietario",
        "Manobravel",
        "Resistencia",
        "Reatancia",
        "Susceptancia",
        "Tap",
        "Tap_Minimo",
        "Tap_Maximo",
        "Defasagem",
        "Barra_Controlada",
        "Capacidade_Normal",
        "Capacidade_em_Emergencia",
        "Numero_de_Taps",
        "Capacidade_de_Equipamento",
        "Agregador_1",
        "Agregador_2",
        "Agregador_3",
        "Agregador_4",
        "Agregador_5",
        "Agregador_6",
        "Agregador_7",
        "Agregador_8",
        "Agregador_9",
        "Agregador_10",
    ],
)

CODES_DICT = {
    DARE: DARE_FIELDS(3, -4, 6, -5, 36, -1, 6, -1, 6),
    DBAR: DBAR_FIELDS(
        5,  # Número
        1,  # Operação
        1,  # Estado
        1,  # Tipo
        2,  # Grupo Base de Tensão
        12,  # Nome
        2,  # Grupo Limite de Tensão
        4,  # Tensão
        4,  # Ângulo
        5,  # Geração Ativa
        5,  # Geração Reativa
        5,  # Geração Reativa Mínima
        5,  # Geração Reativa Máxima
        6,  # Barra Controlada
        5,  # Carga Ativa
        5,  # Carga Reativa
        5,  # Capacitor Reator
        3,  # Área
        4,  # Tensão Para Definição de Carga
        1,  # Modo de Visualização
        3,  # Agregador 1
        3,  # Agregador 2
        3,  # Agregador 3
        3,  # Agregador 4
        3,  # Agregador 5
        3,  # Agregador 6
        3,  # Agregador 7
        3,  # Agregador 8
        3,  # Agregador 9
        3,  # Agregador 10
    ),
    DGBT: DGBT_FIELDS(2, 5),
    DLIN: DLIN_FIELDS(
        5,
        1,
        -1,
        1,
        -1,
        1,
        5,
        2,
        1,
        1,
        1,
        6,
        6,
        6,
        5,
        5,
        5,
        5,
        6,
        4,
        4,
        2,
        4,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
    ),
}
