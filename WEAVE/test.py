import os
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.ticker import MaxNLocator

from pylidar_tls_canopy import riegl_io, plant_profile, grid

import pandas as pd
import openpyxl
from pathlib import Path
import shutil
import timeit
start = timeit.timeit()
os.chdir('/mnt/c/users/kdayal/Documents/2_data/Bosland/4_TLS/1_AT_TMS/plot1/')


poss = pd.read_excel('/mnt/c/Users/kdayal/OneDrive - UGent/Bureaublad/SPs.xlsx', usecols=[0], header=None)
poss = poss.iloc[:,0].values.tolist()


for up, tilt in zip(poss[::2][0:1], poss[::2][0:1]):
    if (len(str(up))==2):
        up=str(0)+str(up)

    if (len(str(tilt))==2):
        tilt=str(0)+str(tilt)


    upright_pth = 'SCANS/ScanPos' + str(up) +'/SINGLESCANS/'
    fnameup = Path(os.listdir(upright_pth)[1]).stem
    upright_rxp_fn = upright_pth + fnameup + '.rxp'
    upright_rdbx_fn = 'project.rdb/SCANS/ScanPos'+ str(up) + '/SINGLESCANS/' + fnameup + '/' + fnameup + '.rdbx'
    upright_transform_fn = 'Site01/ScanPos' + str(up) + '.DAT'


   # shutil.copy(upright_rxp_fn, '/mnt/c/Users/kdayal/Documents/2_data/Bosland/4_TLS/1_AT_TMS/TMS/plot1/rxp/')
   # shutil.copy(upright_rdbx_fn, '/mnt/c/Users/kdayal/Documents/2_data/Bosland/4_TLS/1_AT_TMS/TMS/plot1/rdbx/')
   # shutil.copy(upright_transform_fn, '/mnt/c/Users/kdayal/Documents/2_data/Bosland/4_TLS/1_AT_TMS/TMS/plot1/mats/')


    #fnamet = Path(os.listdir('SCANS/ScanPos' + post +'/SINGLESCANS/')[1]).stem

    tilt_pth = 'SCANS/ScanPos' + str(tilt) +'/SINGLESCANS/'
    fnamet = Path(os.listdir(tilt_pth)[1]).stem
    tilt_rxp_fn = tilt_pth + fnamet + '.rxp'
    tilt_rdbx_fn = 'project.rdb/SCANS/ScanPos'+ str(tilt) + '/SINGLESCANS/' + fnamet + '/' + fnamet + '.rdbx'
    tilt_transform_fn = 'Site01/ScanPos' + str(tilt) + '.DAT'



    # Determine the origin coordinates to use
    # The transformation matrix is read as an array
    transform_matrix = riegl_io.read_transform_file(upright_transform_fn)

    # Extract the translation vector
    x0,y0,z0,_ = transform_matrix[3,:]

    grid_extent = 60
    grid_resolution = 1
    grid_origin = [x0,y0]

transform_matrix