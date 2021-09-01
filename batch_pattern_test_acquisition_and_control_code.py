# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:59:22 2020

@author: aunal
"""

import pyvisa
import sys
from time import time, sleep
from datetime import datetime
import numpy as np
import csv
import os
import serial
from rohde_and_schwarz_HMP4040 import HMP4040
from AIM_TTI_TG5012A import TG5012A
from keithley_model2000 import Keithley

ser = serial.Serial('COM6', 9600, timeout = 2)
ser.flush() 

rm = pyvisa.ResourceManager()

power_sup_address = 'ASRL5::INSTR'
keithley_address = 'ASRL4::INSTR'
pulse_gen_address = 'TCPIP::dcct-pulse-generator.cern.ch::9221::SOCKET' 

pulse_generator = TG5012A(rm, pulse_gen_address)
print('connection to {} is succesful'.format(pulse_generator.IDN()))
keith = Keithley(rm, keithley_address) 
print('connection to {} is succesful'.format(keith.IDN()))
power_supply = HMP4040(rm, power_sup_address)
print('connection to {} is succesful'.format(power_supply.IDN()))

keith.keithley_specifications()

def set_pulse_generator():
    
    pulse_generator.choose_channel(2)
    pulse_generator.choose_wave_type('SQUARE')
    pulse_generator.period(0.00009)
    pulse_generator.amplitude(5)
    pulse_generator.dc_offset(2.5)
    pulse_generator.output_load(50)
    pulse_generator.duty_cycle_for_square_wave(20)
    pulse_generator.output_state('OFF') 
     
def control_pulse_generator(width):
       
    pulse_generator.duty_cycle_for_square_wave(width)

    
def initiate_power_supply():
    
    for i in range(3):

        power_supply.select_channel(i+1)
        power_supply.set_voltage_value(0)
        power_supply.send_command("OUTPut:SELect 1")
        #power_supply.send_command("OUTPut:SELect 0")
        power_supply.send_command("OUTPut:STATe 1")
        

    
def turn_off_power_supply(selected_channels):
     
    number_of_channels = len(selected_channels) 
    
    for i in range(number_of_channels):
        
        power_supply.turn_on_off_output(i)
        power_supply.set_voltage_value(0)
        power_supply.send_command("OUTPut:SELect 0")
    
    
def control_power_supply(voltage_level):
    
    voltage_level = int(voltage_level)
      
    if voltage_level <= 30:
        
        power_supply.select_channel(3)
        power_supply.set_voltage_value(voltage_level)
        power_supply.send_command("OUTPut:SELect ")
        power_supply.turn_on_off_output('ON')
    
    elif voltage_level > 30 and voltage_level <= 60:
        
        channel2 = voltage_level - 30
        power_supply.select_channel(3)
        power_supply.set_voltage_value(30)
        power_supply.select_channel(2)
        power_supply.set_voltage_value(channel2)
        power_supply.send_command("OUTPut:SELect 1")
        power_supply.turn_on_off_output('ON')
        
    elif voltage_level > 60 and voltage_level <= 90:
        
        channel1 = voltage_level - 60
        power_supply.select_channel(3)
        power_supply.set_voltage_value(30)
        power_supply.select_channel(2)
        power_supply.set_voltage_value(30)
        power_supply.select_channel(1)
        power_supply.set_voltage_value(channel1)
        power_supply.send_command("OUTPut:SELect 1")
        power_supply.turn_on_off_output('ON')
        
    else:
        print("UNKNOWN COMMAND!")
        sys.exit()
                  
    
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

def acquisition_control(duration, csv_path, channel_numbers, power_supply_voltage_list, width_list):
        
    now = datetime.now().strftime("%H:%M:%S")                                                                                      
    start_time = now
    min_timer = 0 
    range_counter = 0
    width_counter = 0
    const1 = 0
    const2 = 0
    volt_counter = 0
    voltage_list = []

    features = ["time", "voltage_level[V]", "width[percent]", "RANGE1[V]", "RANGE2[V]", "RANGE3[V]", "RANGE4[V]", "output_signal[V]", "24bit[bin]"]                                  

    with open(csv_path + "\\data.csv", "w") as csv_file:                                                                           
        csv_writer = csv.DictWriter(csv_file, fieldnames = features)
        csv_writer.writeheader()
    
    print("Data Acquisition starts")
    print("Start time = ", start_time)
    print("\n")
    
    loop_start_time = time()
    sec_counter = 0 
    first_volt_value = 1
    control_power_supply(str(first_volt_value))
    csv_volt = "1"
    csv_width = "20"
    
    while min_timer != duration : 
        
        loop_now_time = time()
        now = datetime.now().strftime("%H:%M:%S")
        
        if abs(int(loop_now_time) - int(loop_start_time)) >= 5 :
            
            print("now = ", now)
            loop_start_time = time()
            
            if sec_counter % 60 == 0 and sec_counter != 0 :
                min_timer += 1
                
            if min_timer % 5 == 0 and const1 == 0:
                
                print(str(min_timer) + " minutes pass")
                print("Number of values for each DCCT's ranges = ", str(range_counter))
                const1 = 1
                
            elif min_timer % 5 != 0 and const1 == 1:
                const1 = 0                
                
            if min_timer % 7 == 0 and const2 == 0 and min_timer != 0:
                                
                const2 = 1
                width_counter += 1
                
                if width_counter == 7:
                    
                    width_counter = 0
                    width = width_list[width_counter]
                    csv_width = str(width)
                    control_pulse_generator(width)
                    voltage_lvl = power_supply_voltage_list[volt_counter]
                    csv_volt = str(voltage_lvl)
                    control_power_supply(voltage_lvl) 
                    volt_counter += 1
                    
                else:
                    width = width_list[width_counter]
                    control_pulse_generator(width)
                    csv_width = str(width)
                    
                
            elif min_timer % 7 != 0 and const2 == 1:
                const2 = 0
            
            for i in range(5):
                
                channel = i + 1
                keith.close_channel(channel)                                                             
                sleep(0.8)
                value = keith.read_data()
                voltage_list.append(value)
                print("range" + str(channel) + " = " + value )
                    
            range_counter += 1
            adc = abs(read_24bit(csv_path))
            
            with open(csv_path + "\\data.csv", "a") as csv_files:  
                                                              
                csv_writer = csv.DictWriter(csv_files, fieldnames = features)
                info = {
                        "time" : now,
                        "voltage_level[V]" : csv_volt,
                        "width[percent]" : csv_width,
                        "RANGE1[V]" : voltage_list[0],
                        "RANGE2[V]" : voltage_list[1],
                        "RANGE3[V]" : voltage_list[2],
                        "RANGE4[V]" : voltage_list[3],
                        "output_signal[V]" : voltage_list[4],
                        "24bit[bin]" : adc
                        }
                csv_writer.writerow(info)
                
            sec_counter += 5 
            print(adc)
            print("min: ", min_timer)
            print(width_counter)
            voltage_list.clear()                                                                                                
                
    print("FINISH")
    print("-------------------------------------------------------------------------------")
    pulse_generator.write("OUTPUT OFF")
    turn_off_power_supply(channel_numbers)

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

    channels = [1, 2, 3]   
    power_supply_voltage_list = list(np.arange(2, 71, 1))    
    width_list = [20, 30, 40, 50, 60, 70, 80]
        
    duration = len(width_list) * len(power_supply_voltage_list) * 7
    
    initiate_power_supply()
    sleep(1) 
    set_pulse_generator()
    sleep(1) 
    acquisition_control(duration, path, channels, power_supply_voltage_list, width_list)