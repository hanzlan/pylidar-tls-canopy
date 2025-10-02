import os


import numpy as np
import glob

import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.ticker import MaxNLocator

from pylidar_tls_canopy import riegl_io, plant_profile, grid

import pandas as pd
#import openpyxl
from pathlib import Path
import shutil
import math
import timeit
import riegl_rdb
import ast


upright_rdbx_fn = '/Stor2/karun/data/filtering_tests/louise/'
upright_rxp_fn = '/Stor2/karun/data/filtering_tests/converted/230309_092424.rxp'
upright_transform_fn = '/Stor2/karun/data/synthesis/ScanPosVer.DAT'


#tilt_rdbx_fn = scans['rdb_h']
#tilt_rxp_fn = scans['rxp_h']
#tilt_transform_fn = scans['dat_h']
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

vpp.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)


hinge_pai = vpp.calcHingePlantProfiles()
weighted_pai = vpp.calcSolidAnglePlantProfiles()
linear_pai = vpp.calcLinearPlantProfiles()

hinge_pavd = vpp.get_pavd(hinge_pai)
linear_pavd = vpp.get_pavd(linear_pai)
weighted_pavd = vpp.get_pavd(weighted_pai)



prof_dict_reimported = {"hinge_pai":hinge_pai, 
            "weighted_pai":weighted_pai, 
            "linear_pai":linear_pai, 
            "hinge_pavd":hinge_pavd, 
            "linear_pavd":weighted_pavd, 
            "weighted_pavd": linear_pavd}




prof_dict_notcon['hinge_pai'][-1]
prof_dict_con['hinge_pai'][-1]
prof_dict_ex['hinge_pai'][-1]
prof_dict_conim['hinge_pai'][-1]


  
prof_dict_reimported['hinge_pai'][-1]