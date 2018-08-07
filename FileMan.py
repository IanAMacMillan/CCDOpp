import numpy as np
from astropy.io import fits
import os, os.path
import time
from time import gmtime
from astropy.time import Time

def makeDir():
	folder=time.strftime("%d-%m-%y", gmtime())
	path="/home/ian/Desktop/CCDOpp/Data/"
	directory = path+folder
	if not os.path.exists(directory):
		os.makedirs(directory)
	elif os.path.exists(directory):
		print("Directory already exists")
	dirpath=path+folder+"/"
	return dirpath

def getDir():
	folder=time.strftime("%d-%m-%y", gmtime())
	path="/home/ian/Desktop/CCDOpp/Data/"
	directory = path+folder
	if not os.path.exists(directory):
		newDir=makeDir()
		print("Directory does not exist. New directory made.")
		return newDir
	dirpath=path+folder+"/"
	return dirpath

def newFName():
	imgdir="/home/ian/Desktop/CCDOpp/Data/"
	folder_name=time.strftime("%d-%m-%y", gmtime())
	file_path=imgdir+folder_name
	files=os.listdir(file_path)
	rawlist=[]
	for file in files:
		if file.startswith("IMG_"+folder_name):
			rawlist.append(file)
	count=len(rawlist)+1
	return time.strftime("IMG_%d-%m-%y_"+str(count), gmtime())+".fits"

def saveFile(data, dir=getDir(), fname=newFName()):
    data.writeto(dir+fname)

def newSCIFName(IMGName):
	if isinstance(IMGName, (list,)):
		if len(IMGName)>=1:
			newName=[]
			for x in IMGName:
				newName.append(x.replace("IMG","SCI"))
			return newName
	elif isinstance(IMGName, (str,)):
		return IMGName.replace("IMG","SCI")

#takes a directory and returns the directory and file of all files in a list
def listFile(dir=getDir()):
	list_fname=os.listdir(dir) #makes list of images
	return [dir+file for file in list_fname]

#takes a directory and returns the a list of all files in that directory
def listFileMD(dir=getDir()):
    return os.listdir(dir) #makes list of images

#returns list of data of fits images when given a list of their directories and filenames
def listFNameData(list_fname):
    img_list = [] #list of the data in fits images and their headers
    for x in list_fname:
        file=fits.open(x)
        img_list.append(file[0].data)
        file.close(x)
    return img_list

#takes a directory and returns the data of all files in that directory
def listDirData(dir=getDir()):
	files=listFile(dir)
	return listFNameData(files)

#Takes in an exposure time and a directory and returns a list with the full directory and file name of all dark images with that exposure time
def listDarks(exp, dir=getDir()):
	dark_images=os.listdir(dir+'/')
	d_list= []
	for x in dark_images:
		file=fits.open(dir+'/'+x)
		if file[0].header['exptime'] == exp and file[0].header['FRAME'] == 'Dark':
			d_list.append(dir+'/'+x)
		file.close()
	if len(d_list)==0:
		print("Could not find any files with that exposure time in ")
	return d_list

#returns the name and directory of the nth last image taken (n=1 returns the last image taken)
def lastF(n=1):
	dir=getDir()
	dirlist=listFile(dir)
	folder_name=time.strftime("%d-%m-%y", gmtime())
	count=0
	for x in dirlist:
		if "IMG_"+folder_name in x:
			count=count+1
	if count>0:
		return "IMG_"+folder_name+"_"+str(count-n+1)+".fits"
	elif count==0:
		print("There are no images in this folder.")
		return

def addKeyword(id,val,file=lastF(),dir=getDir()):
	file_name = dir + file
	hdu_list = fits.open(file_name)
	header=hdu_list[0].header
	data=hdu_list[0].data
	if len(id)>8:
		print('Identifiers greater than 8 letters breaks the fit standard')
	hdu_list[0].header[id]=val
	newfile_hdu = fits.PrimaryHDU(hdu_list[0].data, header = header)
	newfile_hdu.writeto(file_name, overwrite = True)

#gets current Modified Julian Date
def getMJD():
	timestr=time.strftime("%Y-%m-%dT%H:%M:%S", gmtime())
	t=Time(timestr, format='isot', scale='utc')
	return t.mjd
