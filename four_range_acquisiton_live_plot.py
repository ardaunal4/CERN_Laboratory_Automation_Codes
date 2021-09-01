import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from matplotlib.animation import FuncAnimation 

""" Real time ploting function from csv file """

now = str(datetime.now().strftime("%D"))
date_of_path = now[3:5] + '-' + now[0:2] + '-' + now[6:8]
csv_path = r"C:\\Users\\aunal\\Desktop\\datas\\First_4_Range"    
path = csv_path + "\\" + date_of_path
csv_name = path + '\\data.csv'

fig, axs = plt.subplots(2, 2, figsize = (15, 9))

def animate(i):
    data = pd.read_csv(csv_name)
    time = data["time"]
    range1 = data["range1"]
    range2 = data["range2"]
    range3 = data['range3']
    range4 = data['range4']
    plt.cla()
    axs[0, 0].plot(time, range1, color = 'blue', linewidth = 0.5)
    axs[0,0].set_title('range1')
    axs[0, 1].plot(time, range2, color = 'red', linewidth = 0.5)
    axs[0,1].set_title('range2')
    axs[1, 0].plot(time, range3, color = 'green', linewidth = 0.5)
    axs[1, 0].set_title('range3')
    axs[1, 1].plot(time, range4, color = 'orange', linewidth = 0.5, alpha = 1)
    axs[1, 1].set_title('range4')
    

ani = FuncAnimation(plt.gcf(), animate)
plt.tight_layout()
plt.show()