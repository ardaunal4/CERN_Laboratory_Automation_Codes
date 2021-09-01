# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 12:41:13 2020

@author: aunal
"""


import pyvisa
from time import time, sleep
from datetime import datetime
import numpy as np 
import csv
import os
import serial


rm = pyvisa.ResourceManager()
gs = rm.open_resource('TCPIP0::dcctyoko1.cern.ch::inst0::INSTR')
keith = rm.open_resource('ASRL4::INSTR', send_end = True)                                                                         # send_end = True means that eoi opened
ser = serial.Serial('COM6', 9600, timeout = 2)
ser.flush() 
                                                                              
def initiate_current_source(current):
    """Initiate current source function. 
        It has a paramater which is current.
        current example : 1E-3 is equal to 1 mA and
        current should be string. """
    gs.write(":SENSe:ZERO:EXECute")
    gs.write_termination = '\n'
    gs.write(":SOUR:Range 200E-3")
    print(gs.query("*IDN?") + ' started succesfully!')
    gs.write(":SOURce:FUNCtion CURRent")
    gs.write(":SOUR:LEVel " + current)
    gs.write(":OUTP:STAT on")
    gs.close()

    
def control_current_source(current):
    """ This function change current level of current source. 
        It has a paramater which is current.
        current example : 1E-3 is equal to 1 mA and
        current should be string """
    gs = rm.open_resource('TCPIP0::dcctyoko1.cern.ch::inst0::INSTR')
        
    if float(current) < 1E-3:
        source_range = 1E-3
    elif float(current) < 10E-3:
        source_range = 10E-3
    elif float(current) < 100E-3:
        source_range = 100E-3
    else:
        source_range = 200E-3
        
    gs.write(":SOUR:Range {}".format(str(source_range)))
    gs.write(":SOUR:LEVel " + current)
    print("Current level is : ", current)
    gs.write(":OUTP:STAT on")
    gs.close()


def initiate_keithley():
    """ Open Keithley function."""
    keith.write("++rst")
    keith.write("++clr")
    keith.write('++addr 4')                                                                                                         # Specifies the address of Keithley
    #keith.write("*cls")
    keith.timeout = 25  
    keith.write("++auto 0")                                                                                                         # Closes read after write
    keith.write("++eoi 1")                                                                                                          # Ends of insertion
    keith.write("++eos 0")                                                                                                          # Appends CR+LF to instrument commands 
    keith.read_termination = '\n'
    keith.write_termination = '\n'
#    keith.write("*IDN?")                                                                                                           # Sends a query command to the multimeter
#    value = keith.write('++read eoi')                                                                                                       # Sends read command to the Prologix which says there is a query
#    value = keith.read()
    sleep(2)
    keith.write(":SENSe:FUNCtion 'VOLTage:DC'")
    keith.write("SENse:VOLTage:DC:RANGe:AUTO OFF")
    keith.write("SENSe:VOLTage:DC:RANGe:UPPer 10") 
    print('Keithley started succesfully')    
    
def read_24bit(csv_path):
    error_now = datetime.now().strftime("%H:%M:%S")
    try: 
        ser.flushInput()
        ser.write(b"a")
        ser_bytes = ser.readline() 
        decoded_bytes = int(ser_bytes[0:len(ser_bytes) - 1].decode("utf-8"))
    except ValueError:
        f = open(csv_path + "\\errors.txt", "a")
        error_message = "Error raised at " + error_now + "n"
        f.write(error_message)
        f.close()
        print('Data could not be read')
        decoded_bytes = 0
    return decoded_bytes


def acquisition_control(duration, csv_path, time_list, current_list):
    """ After connect both current source and multimeter,
        this function can used for read data from multimeter,
        change current level of current source and write data
        into a CSV file. This function focused on real time
        data acquisition.
        USAGE : 
        duration -> duration of process in minutes
        csv_path -> .csv file with path in str
        time_list -> In given time, source will triggered by
        this function to change its current value.
        current -> level of current """
        
    now = datetime.now().strftime("%H:%M:%S")                                                                                        # Specifies time for now in the form of 'Hour:Minutes:Seconds'
    start_time = now
    
    """ Define necessary variables and lists """
    min_timer = 0 
    timer_list_counter = 0
    range_counter = 0
    voltage_list = []
    step = 1
    
    features = ["time", "step", "current[mA]", "RANGE1[V]", "RANGE2[V]", "RANGE3[V]", "RANGE4[V]", "measured_current[V]", "24bit[bin]"]                                        # Columns for csv file

    with open(csv_path + "\\data.csv", "w") as csv_file:                                                                              # Creates and write columns into csv file
        csv_writer = csv.DictWriter(csv_file, fieldnames = features)
        csv_writer.writeheader()
    
    f = open(csv_path + "\\errors.txt", "w")
    f.close()
    
    print("Data Acquisition starts")
    print("Start time = ", start_time)
    print("\n")
    
    loop_start_time = time()
    current_level = '0E-0'
    sec_counter = 0 
    while min_timer != duration : 
        
        loop_now_time = time()
        now = datetime.now().strftime("%H:%M:%S")
        
        if abs(int(loop_now_time) - int(loop_start_time)) >= 5 :                                                                               # This if add 1 second time delay to entire process
            print("now = ", now)
            loop_start_time = time()
            
            if (sec_counter % 6) == 0 : 
                sec_counter = 0
                min_timer += 0.5
                
            if min_timer % 5 == 0:
                print(str(min_timer) + " minutes pass")
                print("Number of values for each DCCT's ranges = ", str(range_counter))
            
            if timer_list_counter < len(time_list) and time_list[timer_list_counter] == min_timer:
                current_level = current_list[timer_list_counter]
                control_current_source(current_level)
                timer_list_counter  += 1
                step += 1
                
            for i in range(5):
                channel = i + 1
                keith.write(":rout:close (@{})".format(channel))                                                                 # Changes number of channel
                sleep(0.7)
                keith.write(":SENSe:DATA?")
                sleep(0.2)
                keith.write('++read eoi') 
                value = keith.read()
                voltage_list.append(value)
                print("range" + str(channel) + " = " + value )
                    
            range_counter += 1
            adc = abs(read_24bit(csv_path))

            with open(csv_path + "\\data.csv", "a") as csv_files:                                                                 # Add taken values into opened CSV file
                csv_writer = csv.DictWriter(csv_files, fieldnames = features)
                info = {
                        "time" : now,
                        "step" : step,
                        "current[mA]" : current_level,
                        "RANGE1[V]" : voltage_list[0],
                        "RANGE2[V]" : voltage_list[1],
                        "RANGE3[V]" : voltage_list[2],
                        "RANGE4[V]" : voltage_list[3],
                        "measured_current[V]" : voltage_list[4],
                        "24bit[bin]" : adc
                        }
                csv_writer.writerow(info)
            sec_counter += 1 
            print(adc)
            voltage_list.clear()                                                                                                 # Clear voltage values list

                
    print("FINISH")
    print("-------------------------------------------------------------------------------")

if __name__ == "__main__":
    
    now = str(datetime.now().strftime("%D"))
    date_of_path = now[3:5] + '-' + now[0:2] + '-' + now[6:8]
    csv_path = "C:\\Users\\aunal\\Desktop\\datas\\First_4_Range"    
    path = csv_path + "\\" + date_of_path
    
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path) 

    duration = 1435                                                                                                           # Duration of acquisition in minutes

    time_list = list(np.arange(1050, 86400, 1050)/60)


    beam_current_list = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065,
                         0.07,0.075, 0.08, 0.085, 0.09, 0.095, 0.1, 0.105, 0.11, 0.115, 0.12, 0.125, 0.13, 0.135,
                         0.14, 0.145, 0.15, 0.155, 0.16, 0.165, 0.17, 0.175, 0.18, 0.185, 0.19, 0.195, 0.2, 0.2, 
                         0.195, 0.19, 0.185, 0.18, 0.175, 0.17, 0.165, 0.16, 0.155, 0.15, 0.145, 0.14, 0.135, 0.13, 
                         0.125, 0.12, 0.115, 0.11, 0.105, 0.1, 0.095, 0.09, 0.085, 0.08, 0.075, 0.07, 0.065, 0.06, 
                         0.055, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02, 0.015, 0.01, 0.005, 0.00E+00]
    
    source_current_list = []
    for current in beam_current_list:
        current = current / 5
        source_current_list.append(str(current))

    current = '0E-0'
    initiate_current_source(current)
    sleep(1)
    initiate_keithley()
    sleep(1) 
    acquisition_control(duration, path, time_list, source_current_list)