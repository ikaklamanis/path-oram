from random import randint
import pprint
import matplotlib.pyplot as plt
import math
import time
from server import simulate, plot_all_simulations

if __name__ == '__main__':

    pp = pprint.PrettyPrinter(indent=4)

    L = 20
    N = 2 ** L 
    total_runs = 500_000
    warmup_runs = 100_000
    sim_runs = total_runs - warmup_runs

    Z_values = [2]
    for Z in Z_values:
        _gtFreqs = simulate(L, N, Z, total_runs, warmup_runs)
    plot_all_simulations(L, N, Z_values, sim_runs)