import queue
import time
import os
import serial
import numpy as np
import threading
import PyDAQmx as nidaq
import matplotlib.pyplot as plt
from scipy import signal

#seting up motor stuff
#most work is outsourced to the Arduino controller, we just send single bytes to tell it which program to run

ser = serial.Serial()
ser.baudrate = 115200
ser.port = ('COM6')
ser.timeout = 0.5 #Increased timeout. I don't think we run into this issue
ser.write_timeout = None #Added this; I think it leads to the annoying noise?
ser.open()

print('Reaching to Ball and Lights Experiment \n Written in Python 3.6 at University of Western Ontario')
print('Last updated 18 Nov 2020 \n \n \n')

#Maybe here add "Resuming a stopped experiment?"
subj_ID = input('Enter Subject ID, format ##: ')

trials = input('Enter number of perturbed trials (Usually 40): ')

print('')
print('')

cond = input('Enter test condition: \n 1 -- Ball \n 2 -- Light \n \n')

if int(cond) != 1:
    if int(cond) != 2:
        cond = input('Please re-enter test condition')


directions = (['CCW', 'NoMovement', 'CW']) #Left, Center, Right
condition = (['Ball', 'Light'])

gprot = input('Generate a new subject protocol? Y/N: ')

p = []

if gprot.find('Y') > -1: #creating a new protocol

    cw = np.zeros(int(trials))
    ccw = np.zeros(int(trials))
    nomove = np.zeros(int(trials))

    cw[:] = int(1)
    ccw[:] = int(-1)

    alltrials = np.hstack((cw,ccw,nomove))

    dprot = np.random.permutation(alltrials)

    np.savetxt(subj_ID + condition[int(cond)-1] +'protocol.txt',np.transpose(dprot), fmt = '%.0f', delimiter = '\t') #save the protocol
    print('Protocol generated for ' + subj_ID + '!')
    p = [subj_ID + condition[int(cond)-1] + 'protocol.txt'] #store the name of the protocol to refer to later

else: #find the existing protocol in the working directory. There needs to be only one, or it will take the first...
    filestosearch = os.listdir()
    for i in filestosearch:
        if i.find(condition[int(cond)-1] + 'Ballprotocol') > -1:
            p += [i]
            print('Using existing protocol: ' + i)
            break
    if p == []:
        print('No protocol found, restart program!')


def nummatches(listoffiles,searchterm): #function looking for matching filenames used when saving files
    
    a = []
    for i in listoffiles:
        if i.find(searchterm) > -1:
            a += [i]
    return len(a)

def get_name(proposedname): #function producing new filenames if duplicates are found

    files = os.listdir()

    a = []
    for i in files:
        if i.find(proposedname) > -1:
            a += [i]        
            
    if len(a) == 0:
        revisedname = proposedname + '1'

    else:
        z = 1
        while 1>0:
            revisedname = proposedname + str((z+1))

            if nummatches(files,revisedname) == 0:
                break
            else:
                z = z+1
    
    return revisedname


#configuring analog inputs:
r = queue.Queue() #this sends all of the data to the to-be-saved file when trial is complete
s = queue.Queue() #this queue is used to collect and move analog data

#prepare analog task to read nine channels
t = nidaq.Task()
t.CreateAIVoltageChan("Dev1/ai0, Dev1/ai1, Dev1/ai2, Dev1/ai3, Dev1/ai16, Dev1/ai26, Dev1/ai28, Dev1/ai22, Dev1/ai40", None, nidaq.DAQmx_Val_RSE, -5, 5, nidaq.DAQmx_Val_Volts, None)
#channel order: Switch, Trigger, Encoder 1, Encoder 2, EMG1, EMG2, EMG3, EMG4, EMG5 (EMG% is the trigger module)
t.CfgSampClkTiming("", 2000, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_ContSamps, 1) #continuous sampling at 2k Hz but probably should turn this down as EMG reconstructs at 1928 sa/sec

read = nidaq.int32()

data = np.zeros(9)
dstream = np.zeros(9)

vistargets = [b'l', b'm', b'r'] #light commands for left, middle (no movement), right
steptargts = [b'a', b'c', b'b'] #motor commands for ccw, no movement, cw

#Threads to save our data

def getanalog():
    dstream = np.zeros(9)
    while read_indicator > 0: #time.clock()-start < 5:
        t.ReadAnalogF64(1, 5, nidaq.DAQmx_Val_GroupByChannel,data, len(data), nidaq.byref(read), None)
        dstream = np.vstack((dstream,data)) #accumulate the data here
        s.put(data[1]) #put the second entry, which is the trigger, into the queue that's read to figure out when to terminate trial 
    print(np.shape(dstream))
    s.queue.clear()
    r.put(dstream) #full datastream
    r.join()
    s.join()

pcol = np.loadtxt(p[0])

#last bit of housekeeping before running the trials: home the motor (for ball) or get the ball out of the way (for lights
# )
if int(cond) == 1: #ball
    print('Homing Motor')
    ser.write(b'h') #home the motor before starting
    time.sleep(5)

if int(cond) == 2: #lights
    print('Turning off Motor')
    ser.write(b'o') #move the stick out of the way and turn off motor
    time.sleep(5)


numberoftrials = len(pcol)
stindex = input('Enter trial to start on (usually should be 1): ')


for i in range(int(stindex)-1,numberoftrials):    


    direction = int(pcol[i]) #read direction out of the protocol file

    anadata = threading.Thread(target = getanalog)

    # Execution for each trial starts here

    indicator = 1
    read_indicator = 1

    print('starting data collection threads')

    data = np.zeros(9) #try reiinitializing these arrays...
    dstream = np.zeros(9)

    t.StartTask()
    anadata.start()
    
    start = time.clock()


    if int(cond) == 2: #lights 

        comd = vistargets[direction]
        ser.write(comd) #sent instruction to arduino, now we log and wait for Arduino to tell us when the participant started 

        while (time.clock()-start < 50): #50 sec timeout if the participant does start
        
            fsensor = s.get() #this is the trigger signal from the arduino
            #print(fsensor) #for debug

            if (fsensor > 4): #lights switched
                time.sleep(1.5)         
                t.StopTask() #stop data collection 1.5 secs after movement
                break

    if int(cond) == 1: #ball

        comd = steptargts[direction]
        ser.write(comd) #sent instruction to arduino, now we log and wait for Arduino to tell us when the participant started 

        while (time.clock()-start < 50): #50 sec timeout
        
            fsensor = s.get() #this is the trigger signal from the arduino
            print(fsensor)

            if (fsensor > 4): #motor started moving
                time.sleep(1.5)         
                t.StopTask() #stop data collection
                break

    read_indicator = -1 #this stops some of the data collection on the backend 

    dstream = r.get() #pull all accumulated data out of the queue where it was collected
    s.task_done() #terminate the queues
    r.task_done()

    print('tasks done!')

    dstream = np.transpose(dstream)

    print(np.shape(dstream)) #to debug; shows the size of the data array from the present trial

    #at this point we check for existing save name and find a new one if necessary
    proposedname = 'S' + subj_ID + condition[int(cond)-1] + directions[direction] + '_' 
    #condition index -1 because the options are 1 and 2; direction should be correct as-is

    revisedname = get_name(proposedname)

    np.savetxt(revisedname + '.txt',dstream, fmt = '%.10f', delimiter = '\t')

    t.StopTask()
    
    if i == numberoftrials-1:
        print('Trial ' + str(i+1) + ' Completed and data logged as: ' + revisedname)
        print('Test completed!')
    else:
        print('Trial ' + str(i+1) + ' Completed and data logged as: ' + revisedname)
        input('Press ENTER to continue') #we go to the top of the loop immediately after ENTER