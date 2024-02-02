import os, csv, math as m
from utils.contants import *
from icecream import ic


def bus_data(data_csv_dir: os.PathLike):
    bus_data_dict = dict()
    with open(data_csv_dir, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=",", quotechar="#")
        next(spamreader, None)
        for row in spamreader:
            bus_data_dict[int(row[0])] = {
                NAME: row[1],
                VOLTAGE_LEVEL: float(row[2]) if row[2] != "" else 0,
                "FR_P": float(row[3]) if row[3] != "" else 0,
                "FR_T": float(row[4]) if row[4] != "" else 0,
                "RP": float(row[5]) if row[5] != "" else 0,
                "RT": float(row[6]) if row[6] != "" else 0,
                AVERAGE_LOAD: float(row[8]) if row[8] != "" else 0,
                MAX_LOAD: float(row[9]) if row[9] != "" else 0,
                CONSUMERS: int(row[10]) if row[10] != "" else 0,
            }
    return bus_data_dict


def edge_data(data_csv_dir: os.PathLike):
    edge_data_dict = dict()
    with open(data_csv_dir, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=",", quotechar="#")
        next(spamreader, None)
        for row in spamreader:
            edge_id = (int(row[0]), int(row[1]), int(row[2]))
            edge_name = row[3]
            distance = float(row[4]) if row[4] != "" else 0
            permanent_failure_rate = float(row[5]) if row[5] != "" else 0
            temporary_failure_rate = float(row[6]) if row[6] != "" else 0
            repair_time = float(row[7]) if row[7] != "" else 0
            manouver_time = float(row[8]) if row[8] != "" else 0
            protection_time = float(row[9]) if row[9] != "" else 0
            edge_data_dict[edge_id] = {
                NAME: edge_name,
                "KM": distance,
                "FR_P": permanent_failure_rate,
                "FR_T": temporary_failure_rate,
                "RP": repair_time,
                "RT": manouver_time,
            }
    return edge_data_dict
