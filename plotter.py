#!/usr/bin/env python3
# SiliTune, a CPU power manager, by petergu
# plot.py, plotting gathered system data
import matplotlib.pyplot as plt
import csv
import sys
import ast

if __name__ == '__main__':
    filename = None
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        print('Usage: ' + sys.argv[0] + ' <datafile> for normal recorded data')
        sys.exit(1)
    data = []
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            data.append([ast.literal_eval(s) for s in row])
    plt.subplot(221)
    plt.plot(data[0], data[1])
    plt.title("CPU temp [C]")
    plt.subplot(222)
    plt.plot(data[0], data[3])
    plt.title("Battery usage [W]")
    plt.subplot(223)
    for i in range(len(data[2][0])):
        plt.plot(data[0], [x[i] for x in data[2]])
    plt.title("Fan speed(s) [RPM]")
    plt.subplot(224)
    for i in range(len(data[4][0])):
        plt.plot(data[0], [x[i] for x in data[4]])
    plt.title("CPU frequencies [MHz]")
    plt.show()

