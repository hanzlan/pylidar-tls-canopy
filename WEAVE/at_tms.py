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
os.chdir('/mnt/c/users/kdayal/Documents/2_data/1_Bosland/4_TLS/1_AT_TMS/2023-08-11_Bosland_plot3.RiSCAN')
os.chdir('/mnt/s/kdayal/unfiltered/2023-08-21_Bosland_plot2.RiSCAN')


poss = pd.read_excel('/mnt/c/Users/kdayal/OneDrive - UGent/Bureaublad/SPs.xlsx', usecols=[0], header=None)
poss = poss.iloc[:,0].values.tolist()

for up, tilt in zip(poss[::2], poss[::2]):
    if (len(str(up))==2):
        up=str(0)+str(up)

    if (len(str(tilt))==2):
        tilt=str(0)+str(tilt)


    upright_pth = 'SCANS/ScanPos' + str(up) +'/SINGLESCANS/'
    fnameup = Path(sorted(os.listdir(upright_pth))[1]).stem
    upright_rxp_fn = upright_pth + fnameup + '.rxp'
    upright_rdbx_fn = 'project.rdb/SCANS/ScanPos'+ str(up) + '/SINGLESCANS/' + fnameup + '/' + fnameup + '.rdbx'
    upright_transform_fn = 'Site02/ScanPos' + str(up) + '.DAT'


   # shutil.copy(upright_rxp_fn, '/mnt/c/Users/kdayal/Documents/2_data/Bosland/4_TLS/1_AT_TMS/TMS/plot1/rxp/')
   # shutil.copy(upright_rdbx_fn, '/mnt/c/Users/kdayal/Documents/2_data/Bosland/4_TLS/1_AT_TMS/TMS/plot1/rdbx/')
   # shutil.copy(upright_transform_fn, '/mnt/c/Users/kdayal/Documents/2_data/Bosland/4_TLS/1_AT_TMS/TMS/plot1/mats/')


    #fnamet = Path(os.listdir('SCANS/ScanPos' + post +'/SINGLESCANS/')[1]).stem

    tilt_pth = 'SCANS/ScanPos' + str(tilt) +'/SINGLESCANS/'
    fnamet = Path(sorted(os.listdir(tilt_pth))[1]).stem
    tilt_rxp_fn = tilt_pth + fnamet + '.rxp'
    tilt_rdbx_fn = 'project.rdb/SCANS/ScanPos'+ str(tilt) + '/SINGLESCANS/' + fnamet + '/' + fnamet + '.rdbx'
    tilt_transform_fn = 'Site02/ScanPos' + str(tilt) + '.DAT'



    # Determine the origin coordinates to use
    transform_matrix = riegl_io.read_transform_file(upright_transform_fn)
    x0,y0,z0,_ = transform_matrix[3,:]

    grid_extent = 60
    grid_resolution = 1
    grid_origin = [x0,y0]

    # If using RXP files only as input, set rxp to True:
    x,y,z,r = plant_profile.get_min_z_grid([upright_rdbx_fn], 
                                           [upright_transform_fn], 
                                        grid_extent, grid_resolution, grid_origin=grid_origin,
                                        rxp=False)
    # Optional weighting of points by 1 / range
    planefit = plant_profile.plane_fit_hubers(x, y, z, w=1/r)
    #planefit['Summary']

    # If the ground plane is not defined then set ground_plane to None
    # and use the sensor_height argument whe adding scan positions
    vpp = plant_profile.Jupp2009(hres=0.5, zres=5, ares=90, 
                                min_z=35, max_z=70, min_h=0, max_h=50,
                                ground_plane=planefit['Parameters'])

    # If using RXP files only as input, set rdbx_file to None (the default)
    query_str = ['reflectance > -20']
    vpp.add_riegl_scan_position(upright_rxp_fn, upright_transform_fn, sensor_height=None,
        rdbx_file=upright_rdbx_fn, method='WEIGHTED', min_zenith=35, max_zenith=70,
        query_str=query_str)

    # If using RXP files only as input, set rdbx_file to None (the default)
    query_str = ['reflectance > -20']
    vpp.add_riegl_scan_position(tilt_rxp_fn, tilt_transform_fn, sensor_height=None,
        rdbx_file=tilt_rdbx_fn, method='WEIGHTED', min_zenith=5, max_zenith=35,
        query_str=query_str)

    vpp.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)
    weighted_pai = vpp.calcSolidAnglePlantProfiles()
    weighted_pavd = vpp.get_pavd(weighted_pai)

    weighted_pai= pd.DataFrame(weighted_pai)
    weighted_pai.to_csv(str(up)+'pai'+'.csv', sep=',', index=False, encoding='utf-8')

    weighted_pavd= pd.DataFrame(weighted_pavd)
    weighted_pavd.to_csv(str(up)+'pavd'+'.csv', sep=',', index=False, encoding='utf-8')
    
end = timeit.timeit()




fl=pd.read_csv(r'/mnt/s/kdayal/unfiltered/101pavd.csv')










plt.plot(fl)
plt.show()

for i in range(3):
    print(i)



from numpy impoty




fig = plt.figure()
ax = plt.axes(projection='3d')
ax.scatter3D(x, y, z)
plt.show()

