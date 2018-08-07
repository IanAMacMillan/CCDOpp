import numpy as np
from astropy.io import fits
import os, os.path
import time
from time import gmtime
import matplotlib.pyplot as plt
from FileMan import *

#Take in an image ARRAY (NOT AN HDU FILE!!!), remove the overscan, and cut it off
def removeOverscan(image_array):
    overscan_size = 29
    cut_size = 33
    overscan_fit_order = 3
    overscan_vector =  np.median(image_array[:,np.shape(image_array)[1] - overscan_size:], axis = 1)
    row_numbers = range(0, len(overscan_vector)) 
    overscan_fit = np.polyfit(row_numbers, overscan_vector, overscan_fit_order)
    fitted_vector = np.poly1d(overscan_fit)(row_numbers)
    #print 'overscan_fit = ' + str(overscan_fit) 
    #plt.plot(row_numbers, overscan_vector)
    #plt.plot(row_numbers, fitted_vector)
    #plt.show() 
    overscan_corrected_array = (image_array.transpose() - fitted_vector).transpose()[:, 0:np.shape(image_array)[1] - cut_size]
    return overscan_corrected_array 

def readFitsFilesToData(files):
    multiple_files = type(files) is list
    if multiple_files: 
        hduls = [fits.open(file) for file in files]
        headers = [hdul[0].header for hdul in hduls]
        data_arrays = [hdul[0].data for hdul in hduls]
        return [headers, data_arrays]
    else:
        file = files
        hdul = fits.open(file)
        header = hdul[0].header
        data_array = hdul[0].data
        return [header, data_array]



#Measure statistics (med, std) of bias files, and save masters if user prefers 
def computeBiasStats(bias_files, dir=getDir(),
                     master_med_file = 'MSB_med.fits', save_master_med = 1,
                     master_std_file = 'MSB_std.fits', save_master_std = 1,
                     correct_overscan = 1, overwrite = 1):
    headers, data_arrays = readFitsFilesToData(bias_files)
    
    if correct_overscan:
        print 'Correcting overscans...'
        data_arrays = [removeOverscan(array) for array in data_arrays]
    print 'Calculating full system statistics...' 
    total_med = np.median(data_arrays)
    total_std = np.std(data_arrays)
    print 'Calculating master bias...' 
    pixel_by_pixel_stds = np.std(data_arrays, axis = 0)
    pixel_by_pixel_meds = np.median(data_arrays, axis = 0)
    print 'Done' 

    if save_master_med:
        print 'Saving master median to ' + str(dir + master_med_file)
        header = headers[0]
        header['COMBINE'] = ('Median combined bias frames using CCDDataAnalysis.computeBiasStats')
        header['FRAME'] = "Master Bias"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADEFROM'] = len(bias_files)
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        master_med_hdu = fits.PrimaryHDU(pixel_by_pixel_meds, header = header)
        master_med_hdul = fits.HDUList([master_med_hdu])
        master_med_hdul.writeto(dir + master_med_file, overwrite = overwrite)
    if save_master_std:
        print 'Saving master std to ' + str(dir + master_std_file)
        header = headers[0]
        header['COMBINE'] = ('Standard dev of bias frames using CCDDataAnalysis.computeBiasStats')
        header['FRAME'] = "Master Bias"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADE-FRM'] = len(bias_files)
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        master_std_hdu = fits.PrimaryHDU(pixel_by_pixel_stds, header = header)
        master_std_hdul = fits.HDUList([master_std_hdu])
        master_std_hdul.writeto(dir + master_std_file, overwrite = overwrite)
    print 'Done' 
    return [total_med,total_std]

#We assume that the exposure times of all images are the same 
def computeDarkStats(dark_files, dir=getDir(),
	                 master_bias_file = 'MSB_med.fits',
                     master_med_file = 'MSD_med.fits', save_master_med = 1,
                     master_std_file = 'MSD_std.fits', save_master_std = 1,
                     correct_overscan = 1, correct_bias = 1, 
                     overwrite = 1): 
    headers, data_arrays = readFitsFilesToData(dark_files)
    if correct_overscan:
        print 'Correcting overscans...'
        data_arrays = [removeOverscan(array) for array in data_arrays]
    if correct_bias: 
    	print 'Subtracting master bias...'
    	master_bias_header, master_bias_array = readFitsFilesToData(master_bias_file)
        data_arrays = [array - master_bias_array for array in data_arrays]
    exp_time = float(headers[0]['EXPTIME'])
    print 'exp_time = ' + str(exp_time)
    print 'Calculating full system statistics...' 
    total_med = np.median(data_arrays) / exp_time
    total_std = np.std(data_arrays) / exp_time
    print 'Calculating master dark...' 
    pixel_by_pixel_stds = np.std(data_arrays, axis = 0) / exp_time
    pixel_by_pixel_meds = np.median(data_arrays, axis = 0) / exp_time 

    if save_master_med:
        print 'Saving master median to ' + str(dir + master_med_file)
        header = headers[0]
        header['COMBINE'] = ('Median combined dark frames using CCDDataAnalysis.computeDarkStats')
        header['FRAME'] = "Master Dark"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADE-FRM'] = len(dark_files)
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        if correct_bias: header['BIASSUB'] = ('Bias corrected by CCDDataAnalysis.computeDarkStats')
        master_med_hdu = fits.PrimaryHDU(pixel_by_pixel_meds, header = header)
        master_med_hdul = fits.HDUList([master_med_hdu])
        master_med_hdul.writeto(dir + master_med_file, overwrite = overwrite)
    if save_master_std:
        print 'Saving master std to ' + str(dir + master_std_file)
        header = headers[0]
        header['COMBINE'] = ('Standard dev of dark frames using CCDDataAnalysis.computeBiasStats')
        header['FRAME'] = "Master Dark"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADEFROM'] = len(dark_files)
    	header['EXPTIME'] = ('1.0') #We scale things so that we have the per second dark current 
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        if correct_bias: header['BIASSUB'] = ('Bias corrected by CCDDataAnalysis.computeDarkStats')
        master_std_hdu = fits.PrimaryHDU(pixel_by_pixel_stds, header = header)
        master_std_hdul = fits.HDUList([master_std_hdu])
        master_std_hdul.writeto(dir + master_std_file, overwrite = overwrite)
    print 'Done'

    return total_med, total_std, pixel_by_pixel_meds, pixel_by_pixel_stds 

    #We assume that the exposure times of all images are the same 
def computeCameraFlatStats(flat_files, dir=getDir(),
	                       master_bias_file = 'MSB_med.fits',
	                       master_dark_file = 'MSD_med.fits', global_dark_cur = 0.02,
                           master_med_file = 'MSF_cs_med.fit', save_master_med = 1,
                           master_std_file = 'MSF_cs_std.fit', save_master_std = 0,
                           correct_overscan = 1, correct_bias = 1, 
                           correct_dark_img = 1, correct_dark_scr = 0,
                           overwrite = 1): 
    headers, data_arrays = readFitsFilesToData(flat_files)
    exp_times = [float(header['EXPTIME']) for header in headers]
    if correct_overscan:
        print 'Correcting overscans...'
        data_arrays = [removeOverscan(array) for array in data_arrays]
    if correct_bias: 
    	print 'Subtracting master bias...'
    	master_bias_header, master_bias_array = readFitsFilesToData(master_bias_file)
        data_arrays = [array - master_bias_array for array in data_arrays]
    if correct_dark_img:
    	print 'Subtracting master dark image...'
    	master_dark_header, master_dark_array = readFitsFilesToData(master_dark_file)
    	dark_time = float(master_dark_header['EXPTIME'])
    	data_arrays = [data_arrays[i] - master_dark_array * exp_times[i] / dark_time for i in range(len(data_arrays))]
    elif correct_dark_scr:
    	print 'Subtracting master dark current..'
    	data_arrays = [data_arrays[i] - master_dark_array * exp_times[i] / dark_time for i in range(len(data_arrays))]

    print 'Calculating full system statistics...' 
    total_med = np.median(data_arrays)
    total_std = np.std(data_arrays)
    print 'Calculating master camera flat...' 
    pixel_by_pixel_meds = np.median(data_arrays, axis = 0) 
    med_comb_val = np.median(pixel_by_pixel_meds)
    pixel_by_pixel_meds = pixel_by_pixel_meds / med_comb_val 
    pixel_by_pixel_stds = np.std(data_arrays, axis = 0) / med_comb_val 

    if save_master_med:
        print 'Saving master median to ' + str(dir + master_med_file)
        header = headers[0]
        header['COMBINE'] = ('Median combined image flat frames using CCDDataAnalysis.computeFlatStats')
        header['FRAME'] = "Master Image Flat"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADE-FRM'] = len(flat_files)
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        if correct_bias: header['BIASSUB'] = ('Bias corrected by CCDDataAnalysis.computeDarkStats')
        if correct_dark_img: header['DARKSUB'] = ('Dark corrected by master dark image subtraction by CCDDataAnalysis.computeDarkStats')
        elif correct_dark_scr: header['DARKSUB'] = ('Dark corrected by master dark current subtraction by CCDDataAnalysis.computeDarkStats')
        master_med_hdu = fits.PrimaryHDU(pixel_by_pixel_meds, header = header)
        master_med_hdul = fits.HDUList([master_med_hdu])
        master_med_hdul.writeto(dir + master_med_file, overwrite = overwrite)
    if save_master_std:
        print 'Saving master std to ' + str(dir + master_std_file)
        header = headers[0]
        header['COMBINE'] = ('Standard dev of dark frames using CCDDataAnalysis.computeBiasStats')
        header['FRAME'] = "Master Dark"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADE-FRM'] = len(dark_files)
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        if correct_bias: header['BIASSUB'] = ('Bias corrected by CCDDataAnalysis.computeDarkStats')
        if correct_dark_img: header['DARKSUB'] = ('Dark corrected by master dark image subtraction by CCDDataAnalysis.computeDarkStats')
        elif correct_dark_scr: header['DARKSUB'] = ('Dark corrected by master dark current subtraction by CCDDataAnalysis.computeDarkStats')
        master_std_hdu = fits.PrimaryHDU(pixel_by_pixel_stds, header = header)
        master_std_hdul = fits.HDUList([master_std_hdu])
        master_std_hdul.writeto(dir + master_std_file, overwrite = overwrite)
    print 'Done' 

    return total_med, total_std, pixel_by_pixel_meds, pixel_by_pixel_stds 
    

    #We assume that the exposure times of all images are the same 
def computeSystemFlatStats(image_files, dir=getDir(),
	                       master_bias_file = 'MSB_med.fits',
	                       master_dark_file = 'MSD_med.fits', global_dark_cur = 0.02,
	                       master_flat_file = 'MSF_cs_med.fits',
                           master_med_file = 'MSF_ss_med.fits', save_master_med = 1,
                           master_std_file = 'MSF_ss_std.fits', save_master_std = 0,
                           correct_overscan = 1, correct_bias = 1, 
                           correct_dark_img = 1, correct_dark_scr = 0,
                           correct_cam_flat = 1,
                           overwrite = 1): 
    headers, data_arrays = readFitsFilesToData(flat_files)
    exp_times = [float(header['EXPTIME']) for header in headers]
    if correct_overscan:
        print 'Correcting overscans...'
        data_arrays = [removeOverscan(array) for array in data_arrays]
    if correct_bias: 
    	print 'Subtracting master bias...'
    	master_bias_header, master_bias_array = readFitsFilesToData(master_bias_file)
        data_arrays = [array - master_bias_array for array in data_arrays]
    if correct_dark_img:
    	print 'Subtracting master dark image...'
    	master_dark_header, master_dark_array = readFitsFilesToData(master_dark_file)
    	data_arrays = [data_arrays[i] - master_dark_array * exp_times[i] for i in range(len(data_arrays))]
    elif correct_dark_scr:
    	print 'Subtracting master dark current..'
    	data_arrays = [data_arrays[i] - master_dark_array * exp_times[i] for i in range(len(data_arrays))]
    if correct_cam_flat:
    	print 'Normalizing by camera flat'
    	master_camera_flat_header, master_camera_flat_array = readFitsFilesToData(master_flat_file)
    	master_camara_flat_array = master_camera_flat_array / np.median(master_camera_flat_array)
    	data_arrays = [array / master_camera_flat_array for array in data_arrays]

    print 'Calculating full system statistics...' 
    total_med = np.median(data_arrays)
    total_std = np.std(data_arrays)
    print 'Calculating master camera flat...' 
    pixel_by_pixel_meds = np.median(data_arrays, axis = 0) 
    pixel_by_pixel_stds = np.std(data_arrays, axis = 0) 

    if save_master_med:
        print 'Saving master median to ' + str(dir + master_med_file)
        header = headers[0]
        header['COMBINE'] = ('Median combined image flat frames using CCDDataAnalysis.computeFlatStats')
        header['FRAME'] = "Master Image Flat"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADE-FRM'] = len(flat_files)
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        if correct_bias: header['BIASSUB'] = ('Bias corrected by CCDDataAnalysis.computeDarkStats')
        if correct_dark_img: header['DARKSUB'] = ('Dark corrected by master dark image subtraction by CCDDataAnalysis.computeDarkStats')
        elif correct_dark_scr: header['DARKSUB'] = ('Dark corrected by master dark current subtraction by CCDDataAnalysis.computeDarkStats')
        if correct_cam_flat: header['CAMFLAT'] = ('Camera flat corrected by camera flat image normalized by CCDDataAnalysis.computeSystemFlatStats')
        master_med_hdu = fits.PrimaryHDU(pixel_by_pixel_meds, header = header)
        master_med_hdul = fits.HDUList([master_med_hdu])
        master_med_hdul.writeto(dir + master_med_file, overwrite = overwrite)
    if save_master_std:
        print 'Saving master std to ' + str(dir + master_std_file)
        header = headers[0]
        header['COMBINE'] = ('Standard dev of dark frames using CCDDataAnalysis.computeBiasStats')
        header['FRAME'] = "Master Dark"
    	header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
    	header['MADE-FRM'] = len(dark_files)
        if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
        if correct_bias: header['BIASSUB'] = ('Bias corrected by CCDDataAnalysis.computeDarkStats')
        if correct_dark_img: header['DARKSUB'] = ('Dark corrected by master dark image subtraction by CCDDataAnalysis.computeDarkStats')
        elif correct_dark_scr: header['DARKSUB'] = ('Dark corrected by master dark current subtraction by CCDDataAnalysis.computeDarkStats')
        if correct_cam_flat: header['CAMFLAT'] = ('Camera flat corrected by camera flat image normalized by CCDDataAnalysis.computeSystemFlatStats')
        master_std_hdu = fits.PrimaryHDU(pixel_by_pixel_stds, header = header)
        master_std_hdul = fits.HDUList([master_std_hdu])
        master_std_hdul.writeto(dir + master_std_file, overwrite = overwrite)
    print 'Done'

    return total_med, total_std, pixel_by_pixel_meds, pixel_by_pixel_stds 

def cleanScienceImage(image_files, dir=getDir(),
	                       save_images = 1, 
	                       master_bias_file = 'MSB_med.fits',
	                       master_dark_file = 'MSD_med.fits', global_dark_cur = 0.02,
	                       master_flat_file = 'MSF_ss_med.fits',
                           correct_overscan = 1, correct_bias = 1, 
                           correct_dark_img = 1, correct_dark_scr = 0,
                           correct_cam_flat = 1,
                           overwrite = 1): 
    cleaned_filen=newSCIFName(image_files)
    headers, data_arrays = readFitsFilesToData(image_files)
    exp_times = [float(header['EXPTIME']) for header in headers]
    if correct_overscan:
        print 'Correcting overscans...'
        data_arrays = [removeOverscan(array) for array in data_arrays]
    if correct_bias: 
    	print 'Subtracting master bias...'
    	master_bias_header, master_bias_array = readFitsFilesToData(master_bias_file)
        data_arrays = [array - master_bias_array for array in data_arrays]
    if correct_dark_img:
    	print 'Subtracting master dark image...'
    	master_dark_header, master_dark_array = readFitsFilesToData(master_dark_file)
    	data_arrays = [data_arrays[i] - master_dark_array * exp_times[i] for i in range(len(data_arrays))]
    elif correct_dark_scr:
    	print 'Subtracting master dark current..'
    	data_arrays = [data_arrays[i] - master_dark_array * exp_times[i] for i in range(len(data_arrays))]
    if correct_cam_flat:
    	print 'Normalizing by camera flat'
    	master_camera_flat_header, master_camera_flat_array = readFitsFilesToData(master_flat_file)
    	master_camara_flat_array = master_camera_flat_array / np.median(master_camera_flat_array)
    	data_arrays = [array / master_camera_flat_array for array in data_arrays]

    if save_images:
    	for i in range(len(cleaned_filen)):
    	    clean_file_name = cleaned_filen[i]
            print 'Saving cleaned_file to ' + str(dir + clean_file_name)
            header = headers[i]
            data_array = data_arrays[i]
            header['FRAME'] = "Cleaned Image"
    	    header['DATE-OBS'] = time.strftime("%y-%m-%dT%H:%M:%S", gmtime())
            if correct_overscan: header['OSCANNED'] = ('Overscan removed by CCDDataAnalysis.removeOverscan')
            if correct_bias: header['BIASSUB'] = ('Bias corrected by CCDDataAnalysis.computeDarkStats')
            if correct_dark_img: header['DARKSUB'] = ('Dark corrected by master dark image subtraction by CCDDataAnalysis.computeDarkStats')
            elif correct_dark_scr: header['DARKSUB'] = ('Dark corrected by master dark current subtraction by CCDDataAnalysis.computeDarkStats')
            if correct_cam_flat: header['CAMFLAT'] = ('Camera flat corrected by camera flat image normalized by CCDDataAnalysis.computeSystemFlatStats')
            cleaned_file_hdu = fits.PrimaryHDU(data_array, header = header)
            cleaned_file_hdul = fits.HDUList([cleaned_file_hdu])
            cleaned_file_hdul.writeto(clean_file_name, overwrite = overwrite)
    print 'Done'
    return data_arrays

#plots and saves a plot of the spectrum of a file given its name and location
def plotSpectra(file=lastF(),dir=getDir()):
    num_col=101
    row_to_plot = 1600
    file_name = dir + file
    hdu_list = fits.open(file_name)
    fits_data = hdu_list[0].data
    a = []
    for i in range(num_col):
        a.append(fits_data[row_to_plot+i])
    nonnp=np.median(a, axis=0)
    toplot=np.array(nonnp)
    plt.plot(range(0, len(toplot)), toplot, linewidth=0.5)
    #plt.ylabel('Flux Density Incident on CCD\n(photon/s/pix/asec^2/m^2)')
    #plt.xlabel('CCD Column Number')
    plotName=file.replace(".fits",".pdf").replace("IMG","PLT")
    plt.savefig(dir+ plotName)
    print("Saved plot as: " + plotName)
    plt.show()
    return toplot.tolist()

#given a file numFulPx returns the number of full pixels
def numFulPx(file=lastF(), dir=getDir(), fulval=65520):
	file_name = dir + file
	hdu_list = fits.open(file_name)
	fits_data = np.array(hdu_list[0].data)
	count=0
	for i in fits_data:
		count=count+np.sum(i >= fulval)
	return count

#given a file it returns a suggested exposure time for the next image. Works best on Bias and dark reduced images.
def autoExp(file=lastF(), dir=getDir()):
	full=65535 #value of full well capacity
	fillto=0.7 #makes the max saturated pixel at this number*100%
	numful=numFulPx(file, dir)
	print('Number of full pixels: '+str(numful))
	file_name = dir + file
	hdu_list = fits.open(file_name)
	header=hdu_list[0].header
	exptime=header['EXPTIME']
	if numful>(int(0.07*full)):
		print('Frame seems to be too saturated. Cut Exposure time in half')
		if exptime<2.0 and numful>(int(0.2*full)):
			print('Image is far to bright.')
			return 1.0
		return round(exptime/2.0,2)
	fits_data = np.array(hdu_list[0].data)
	flat=np.concatenate(fits_data, axis=0)
	numpx=len(flat) #the number of pixels that are in the image
	ninenine=int(0.99999*len(flat))
	tarpx=np.sort(flat)
	curval=tarpx[ninenine]
	sugexp=(exptime/curval)*fillto*full
	if sugexp<=1.0:
		return 1.0
	return round(sugexp,2)





