# -*- coding: utf-8 -*-


import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation 
""" Real time reading function from csv file """

csv_name = "C:\\Users\\aunal\\Desktop\\datas\\RANGE3\\10-03-20\\70_minutes.csv"

def animate(i):
    data = pd.read_csv(csv_name)
    x = data["Time"]
    y = data["Standart_Deviation"]
    z = data["Keithley"]
    plt.cla()
    plt.plot(x, y, label = "Std", color = "red", linewidth = 1, alpha = 1)
    plt.plot(x, z, label = "Voltage", color = "blue", linewidth = 1, alpha = 1)
    plt.legend(loc = "upper right")
    plt.tight_layout()

ani = FuncAnimation(plt.gcf(), animate)
plt.tight_layout()
plt.show()