from collections import namedtuple

StochasticParams = namedtuple(
    "StochasticParams",
    ["PermanentFailureRate", "TemporaryFailureRate", "ReplacementTime", "RepairTime"],
)
