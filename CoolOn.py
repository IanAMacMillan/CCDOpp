import PyIndi
import time
from time import gmtime
import sys
import threading
from astropy.io import fits
import numpy as np
import io
import math

class IndiClient(PyIndi.BaseClient):
    def __init__(self):
        super(IndiClient, self).__init__()
    def newDevice(self, d):
        pass
    def newProperty(self, p):
        pass
    def removeProperty(self, p):
        pass
    def newBLOB(self, bp):
        global blobEvent
        print("new BLOB ", bp.name)
        blobEvent.set()
        pass
    def newSwitch(self, svp):
        pass
    def newNumber(self, nvp):
        pass
    def newText(self, tvp):
        pass
    def newLight(self, lvp):
        pass
    def newMessage(self, d, m):
        pass
    def serverConnected(self):
        pass
    def serverDisconnected(self, code):
        pass

# connect the server
indiclient=IndiClient()
indiclient.setServer("localhost",7624)
 
if (not(indiclient.connectServer())):
     print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
     print("  indiserver indi_simulator_telescope indi_simulator_ccd")
     sys.exit(1)
print("CONNECTED TO SERVER")


ccd="SBIG CCD"
device_ccd=indiclient.getDevice(ccd)
while not(device_ccd):
    time.sleep(0.5)
    device_ccd=indiclient.getDevice(ccd)    
print("GOT CCD DEVICE")


ccd_connect=device_ccd.getSwitch("CONNECTION")
while not(ccd_connect):
    time.sleep(0.5)
    ccd_connect=device_ccd.getSwitch("CONNECTION")
if not(device_ccd.isConnected()):
    ccd_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
    ccd_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
    indiclient.sendNewSwitch(ccd_connect)
print("CONNECTED TO CCD")


#----------------------------------------------------
print("---------------------------------------------")
usr_temp=input("ENTER SET TEMP: ")
print("---------------------------------------------")
#----------------------------------------------------


ccd_temp=device_ccd.getNumber("CCD_TEMPERATURE")
ccd_temp[0].value=usr_temp
indiclient.sendNewNumber(ccd_temp)

ccd_cooler_power = device_ccd.getNumber("CCD_COOLER_POWER")

ccd_cooler=device_ccd.getSwitch("CCD_COOLER")
ccd_cooler[0].s=PyIndi.ISS_ON  # the "COOLER_ON" switch
ccd_cooler[1].s=PyIndi.ISS_OFF # the "COOLER_OFF" switch
indiclient.sendNewSwitch(ccd_cooler)

start=time.time()

ccd_temp = device_ccd.getNumber("CCD_TEMPERATURE")
for g in xrange(1,9000):
    #ccd_temp[0].value=usr_temp
    #indiclient.sendNewNumber(ccd_temp)
    ccd_cooler_power = device_ccd.getNumber("CCD_COOLER_POWER")
    ccd_cooler[0].s=PyIndi.ISS_ON  # the "COOLER_ON" switch
    ccd_cooler[1].s=PyIndi.ISS_OFF # the "COOLER_OFF" switch
    indiclient.sendNewSwitch(ccd_cooler)
    ccd_temp=device_ccd.getNumber("CCD_TEMPERATURE")
    #print('time since start: ' + str(time.time()-start))
    print("CCD cooler power: " + str(math.ceil(ccd_cooler_power[0].value*100)/100) + "%")
    print("CCD Temp: " + str(math.ceil(ccd_temp[0].value*100)/100) + " Degrees Celsius")
    time.sleep(2)
