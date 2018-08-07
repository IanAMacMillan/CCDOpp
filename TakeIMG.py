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


def connectServer():
    indiclient=IndiClient()
    indiclient.setServer("localhost",7624)
    if (not(indiclient.connectServer())):
        print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
        print("Using indiserver indi_simulator_ccd")
        sys.exit(1)
    print("CONNECTED TO SERVER")

def isServerConnected():
    indiclient=IndiClient()
    if (not(indiclient.connectServer())):
        return False
    elif (indiclient.connectServer()):
        return True

def connectCCD():
    indiclient=IndiClient()
    ccd="SBIG CCD"
    device_ccd=indiclient.getDevice(ccd)
    while not(device_ccd):
        time.sleep(0.5)
        device_ccd=indiclient.getDevice(ccd)
    ccd_connect=device_ccd.getSwitch("CONNECTION")
    while not(ccd_connect):
        time.sleep(0.5)
        ccd_connect=device_ccd.getSwitch("CONNECTION")
    if not(device_ccd.isConnected()):
        ccd_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
        ccd_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
        indiclient.sendNewSwitch(ccd_connect)
    print("CONNECTED TO CCD")

def isCCDconnected():
    indiclient=IndiClient()
    ccd="SBIG CCD"
    device_ccd=indiclient.getDevice(ccd)
    indiclient=IndiClient()
    if (not(device_ccd)):
        return False
    elif device_ccd:
        return True

def connect():
    while not(isServerConnected()):
        connectServer()
        time.sleep(1)
    while not(isCCDconnected()):
        connectCCD()
        time.sleep(1)

def setOverscan(oscan=30):
    ccd="SBIG CCD"
    device_ccd=indiclient.getDevice(ccd)
    ccd_frame=device_ccd.getNumber("CCD_FRAME")
    default_width=3326
    defsult_height=2584
    ccd_frame[0].value=0 #Set left-most pixel position
    ccd_frame[1].value=0 #Set top-most pixel position
    ccd_frame[2].value=default_width+oscan  #Set width of frame readout in px
    ccd_frame[3].value=defsult_height+oscan #Set height of frame readout in px
    indiclient.sendNewNumber(ccd_frame)

def takePic(exp):
    indiclient=IndiClient()
    ccd="SBIG CCD"
    device_ccd=indiclient.getDevice(ccd)
    ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
    while not(ccd_exposure):
        time.sleep(0.5)
        ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")

    # we should inform the indi server that we want to receive the
    # "CCD1" blob from this device
    indiclient.setBLOBMode(PyIndi.B_ALSO, ccd, "CCD1")

    ccd_ccd1=device_ccd.getBLOB("CCD1")
    while not(ccd_ccd1):
        time.sleep(0.5)
        ccd_ccd1=device_ccd.getBLOB("CCD1")

    # a list of our exposure times
    exposure=exp

    # we use here the threading.Event facility of Python
    # we define an event for newBlob event
    blobEvent=threading.Event()
    blobEvent.clear()

    ccd_exposure[0].value=exposure
    indiclient.sendNewNumber(ccd_exposure)

    print("THE EXPOSURE IS "+ str(exposure) +" SECONDS")
    # wait for the ith exposure
    blobEvent.wait()
    for blob in ccd_ccd1:
        print(" size: ", blob.size," format: ", blob.format)
        # pyindi-client adds a getblobdata() method to IBLOB item
        # for accessing the contents of the blob, which is a bytearray in Python
        blob_fits=blob.getblobdata()
        #-------------------------------------------------------------------------file management and saving image
        blobfile = io.BytesIO(blob_fits)
        with open(getDir()+ newFName(), "wb") as f:
            f.write(blobfile.getvalue())
    #----------------------------------------------------------------------------bm
    print("EXPOSURE TAKEN AND SAVED AS: " + image_name)
    return image_name+".fit"


def frameType(f): #Takes in a string of the frame type wanted and sets the frame type
    indiclient=IndiClient()
    ccd="SBIG CCD"
    device_ccd=indiclient.getDevice(ccd)
    if f=='L' or 'l' or 'Light' or 'light':
        ccd_frame_reset=device_ccd.getSwitch("CCD_FRAME_TYPE")
        ccd_frame_reset[0].s=PyIndi.ISS_ON   # Sets the frame type to "LIGHT"
        ccd_frame_reset[1].s=PyIndi.ISS_OFF  # Sets the frame type to "BIAS"
        ccd_frame_reset[2].s=PyIndi.ISS_OFF  # Sets the frame type to "DARK"
        ccd_frame_reset[3].s=PyIndi.ISS_OFF  # Sets the frame type to "FLAT"
        indiclient.sendNewSwitch(ccd_frame_reset)
    elif f=='D' or 'd' or 'Dark' or 'dark':
        ccd_frame_reset=device_ccd.getSwitch("CCD_FRAME_TYPE")
        ccd_frame_reset[0].s=PyIndi.ISS_OFF  # Sets the frame type to "LIGHT"
        ccd_frame_reset[1].s=PyIndi.ISS_OFF  # Sets the frame type to "BIAS"
        ccd_frame_reset[2].s=PyIndi.ISS_ON   # Sets the frame type to "DARK"
        ccd_frame_reset[3].s=PyIndi.ISS_OFF  # Sets the frame type to "FLAT"
        indiclient.sendNewSwitch(ccd_frame_reset)
    elif f=='B' or 'b' or 'Bias' or 'bias':
        ccd_frame_reset=device_ccd.getSwitch("CCD_FRAME_TYPE")
        ccd_frame_reset[0].s=PyIndi.ISS_OFF  # Sets the frame type to "LIGHT"
        ccd_frame_reset[1].s=PyIndi.ISS_ON   # Sets the frame type to "BIAS"
        ccd_frame_reset[2].s=PyIndi.ISS_OFF  # Sets the frame type to "DARK"
        ccd_frame_reset[3].s=PyIndi.ISS_OFF  # Sets the frame type to "FLAT"
        indiclient.sendNewSwitch(ccd_frame_reset)
    elif f=='F' or 'f' or 'Flat' or 'flat':
        ccd_frame_reset=device_ccd.getSwitch("CCD_FRAME_TYPE")
        ccd_frame_reset[0].s=PyIndi.ISS_OFF  # Sets the frame type to "LIGHT"
        ccd_frame_reset[1].s=PyIndi.ISS_OFF  # Sets the frame type to "BIAS"
        ccd_frame_reset[2].s=PyIndi.ISS_OFF  # Sets the frame type to "DARK"
        ccd_frame_reset[3].s=PyIndi.ISS_ON  # Sets the frame type to "FLAT"
        indiclient.sendNewSwitch(ccd_frame_reset)

def takeLight(exp):
    if not isServerConnected() and isCCDconnected():
        print("INDIServer and CCD are not connected to the client")
        print("connect INDIServer using the command: connect()")
    if isServerConnected():
        if isCCDconnected():
            frametype('light')
            takePic(exp)
        else:
            print("CCD has not been gotten.")
            print("connect to CCD using the command: connectCCD()")
    else:
        print("INDIServer is not connected to the client")
        print("connect INDIServer using the command: connectServer()")

def takeDark(exp):
    if not isServerConnected() and isCCDconnected():
        print("INDIServer and CCD are not connected to the client")
        print("connect INDIServer using the command: connect()")
    if isServerConnected():
        if isCCDconnected():
            frametype('dark')
            takePic(exp)
        else:
            print("CCD has not been gotten.")
            print("connect to CCD using the command: connectCCD()")
    else:
        print("INDIServer is not connected to the client")
        print("connect INDIServer using the command: connectServer()")

def takeBias():
    if not isServerConnected() and isCCDconnected():
        print("INDIServer and CCD are not connected to the client")
        print("connect INDIServer using the command: connect()")
    if isServerConnected():
        if isCCDconnected():
            frametype('dark')
            takePic(0)
        else:
            print("CCD has not been gotten.")
            print("connect to CCD using the command: connectCCD()")
    else:
        print("INDIServer is not connected to the client")
        print("connect INDIServer using the command: connectServer()")

def takeFlat(exp):
    if not isServerConnected() and isCCDconnected():
        print("INDIServer and CCD are not connected to the client")
        print("connect INDIServer using the command: connect()")
    if isServerConnected():
        if isCCDconnected():
            frametype('dark')
            takePic(exp)
        else:
            print("CCD has not been gotten.")
            print("connect to CCD using the command: connectCCD()")
    else:
        print("INDIServer is not connected to the client.")
        print("connect INDIServer using the command: connectServer()")

def setTemp(temp=-15):
    indiclient=IndiClient()
    ccd="SBIG CCD"
    device_ccd=indiclient.getDevice(ccd)
    ccd_temp=device_ccd.getNumber("CCD_TEMPERATURE")
    print("Current temp: "+ ccd_temp[0].value +"degrees")
    ccd_temp[0].value=temp
    indiclient.sendNewNumber(ccd_temp)
    print("Attempting to set temp to "+ temp +" degrees Celsius")

    while ccd_temp[0].value>temp+2:
        print("Current temp: "+ ccd_temp[0].value +"degrees")
        time.sleep(3)
    print("CCD is close to settemp")

def getTemp():
    indiclient=IndiClient()
    ccd="SBIG CCD"
    device_ccd=indiclient.getDevice(ccd)
    ccd_temp=device_ccd.getNumber("CCD_TEMPERATURE")
    return ccd_temp[0].value



