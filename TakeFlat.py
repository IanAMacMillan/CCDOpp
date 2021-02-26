import PyIndi
import time
import astropy 
from time import gmtime
import sys
import threading
from astropy.io import fits
from astropy.utils.data import download_file
import numpy as np
import io
import matplotlib.pyplot as plt
from FileMan import *

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
    time.sleep(3)
    print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
    print("indiserver using indi_simulator_ccd")
    sys.exit(1)
print("CONNECTED TO SERVER")

ccd="SBIG CCD"
device_ccd=indiclient.getDevice(ccd)
while not(device_ccd):
    time.sleep(0.5)
    device_ccd=indiclient.getDevice(ccd)    
print("RETRIEVED CCD DEVICE")

ccd_connect=device_ccd.getSwitch("CONNECTION")
while not(ccd_connect):
    time.sleep(0.5)
    ccd_connect=device_ccd.getSwitch("CONNECTION")
if not(device_ccd.isConnected()):
    ccd_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
    ccd_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
    indiclient.sendNewSwitch(ccd_connect)
print("CONNECTED TO CCD")

#Resets the frame size
ccd_frame_reset=device_ccd.getSwitch("CCD_FRAME_RESET")
ccd_frame_reset[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
indiclient.sendNewSwitch(ccd_frame_reset)

#This section sets the size of the 
overscan=30 #Overscan in px
ccd_frame=device_ccd.getNumber("CCD_FRAME")
ccd_frame[0].value=0 #Set left-most pixel position
ccd_frame[1].value=0 #Set top-most pixel position
ccd_frame[2].value=3360+overscan #Set width of frame readout in px
ccd_frame[3].value=2584+overscan #Set height of frame readout in px
indiclient.sendNewNumber(ccd_frame)

#Adds binning
hBinning=2 #the horizontal binning number
vBinning=2 #the vertical binning number
ccd_bin=device_ccd.getNumber("CCD_BINNING")
ccd_bin[0].value=hBinning
ccd_bin[1].value=vBinning
indiclient.sendNewNumber(ccd_bin)

ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
while not(ccd_exposure):
    time.sleep(0.5)
    ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")

#inform the indi server that we want to receive the
#"CCD1" blob from this device
indiclient.setBLOBMode(PyIndi.B_ALSO, ccd, "CCD1")
print("SEVER SETUP TO GET BLOB")

ccd_ccd1=device_ccd.getBLOB("CCD1")
while not(ccd_ccd1):
    time.sleep(0.5)
    ccd_ccd1=device_ccd.getBLOB("CCD1")
print("---------------------------------------------")
exp=input("ENTER EXPOSURE TIME: ")
print("---------------------------------------------")




# a list of our exposure times
exposures=[exp for i in range(7)]

ccd_frame_reset=device_ccd.getSwitch("CCD_FRAME_TYPE")
ccd_frame_reset[0].s=PyIndi.ISS_OFF  # Sets the frame type to "LIGHT"
ccd_frame_reset[1].s=PyIndi.ISS_OFF  # Sets the frame type to "BIAS"
ccd_frame_reset[2].s=PyIndi.ISS_OFF  # Sets the frame type to "DARK"
ccd_frame_reset[3].s=PyIndi.ISS_ON  # Sets the frame type to "FLAT"
indiclient.sendNewSwitch(ccd_frame_reset)

ccd_temp=device_ccd.getNumber("CCD_TEMPERATURE")
ccd_temp[0].value=-15
indiclient.sendNewNumber(ccd_temp)

# we use here the threading.Event facility of Python
# we define an event for newBlob event
blobEvent=threading.Event()
blobEvent.clear()

i=0
ccd_exposure[0].value=exposures[i]
indiclient.sendNewNumber(ccd_exposure)
while (i < len(exposures)):
    print("EXPOSURE "+ str(i+1) + " is "+ str(exposures[i]) +" SECONDS")
    # wait for the ith exposure
    blobEvent.wait()
    # we can start immediately the next one
    if (i + 1 < len(exposures)):
        ccd_exposure[0].value=exposures[i+1]
        blobEvent.clear()
        indiclient.sendNewNumber(ccd_exposure)
    # and meanwhile process the received one
    for blob in ccd_ccd1:
        print("name: ", blob.name," size: ", blob.size," format: ", blob.format)
        # pyindi-client adds a getblobdata() method to IBLOB item
        # for accessing the contents of the blob, which is a bytearray in Python
        blob_fits=blob.getblobdata()
        print("fits data type: ", type(blob_fits))
        #-------------------------------------------------------------------------file management and saving image
        blobfile = io.BytesIO(blob_fits)
        # open a file and save buffer to disk
        image_name=newFName()
        dirtosave=getDir()
        with open(getDir()+ image_name, "wb") as f:
            f.write(blobfile.getvalue())
        addKeyword('MJD',str(getMJD()),image_name,dirtosave)

        #----------------------------------------------------------------------------bm
    i+=1
    print("EXPOSURE "+ str(i) + " TAKEN AND SAVED AS: " + image_name)
print("<<<<<<<<<<<<<<<  FINISHED TASK  >>>>>>>>>>>>>>>")
