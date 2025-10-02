import os


import time

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
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from pathlib import Path
from tqdm import tqdm

start = timeit.timeit()


os.chdir(f'/Stor2/karun/data/synthesis/all')


ignore_extensions = [".dat", ".DAT"]

file_data = [] 
for root, dirs, files in os.walk("."):
    for file in files:
        if not any(file.endswith(ext) for ext in ignore_extensions):
            file_data.append({"Full_path": str(os.path.abspath(os.path.join(root, file))), 
                              "Directory": str(root),
                              "File_type": str(os.path.split(root)[1]), 
                              "Scan": str(os.path.splitext(file)[0])})

file_data = pd.DataFrame(file_data)

file_data_rdb = file_data[file_data["File_type"] == "allrdbs2"]

file_data_rxp = file_data[file_data["File_type"] == "allrxps2"]

file_locs = pd.merge(file_data_rxp, file_data_rdb, on='Scan', how='inner')



def get_plantprofiles(rxp, rdb, country, project, scan):
    try:
        upright_rdbx_fn = rdb
        upright_rxp_fn = rxp
        upright_transform_fn = "/Stor2/karun/data/synthesis/ScanPosVer.DAT"
        
        
        # Determine the origin coordinates to use
        transform_matrix = riegl_io.read_transform_file(upright_transform_fn)
        x0,y0,z0,_ = transform_matrix[3,:]

        grid_extent = 60
        grid_resolution = 1
        grid_origin = [x0,y0]
        

        # If using RXP files only as input, set rxp to True:
        x,y,z,r = plant_profile.get_min_z_grid([upright_rxp_fn], 
                                            [upright_transform_fn], 
                                            grid_extent, grid_resolution, grid_origin=grid_origin,
                                            rxp=True)
        
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
        
        prof_dict = {"hinge_pai":hinge_pai, 
                    "weighted_pai":weighted_pai, 
                    "linear_pai":linear_pai, 
                    "hinge_pavd":hinge_pavd, 
                    "linear_pavd":weighted_pavd, 
                    "weighted_pavd": linear_pavd}
        
        
        print("done")
        print("***************************")

        #weighted_pai= pd.DataFrame(weighted_pai)
        #weighted_pai.to_csv(str(up)+'pai'+'.csv', sep=',', index=False, encoding='utf-8')

        #weighted_pavd= pd.DataFrame(weighted_pavd)
        #weighted_pavd.to_csv(str(up)+'pavd'+'.csv', sep=',', index=False, encoding='utf-8')
        
        df = pd.DataFrame(prof_dict)
        name = "/home/kdayal/projects/pylidar-tls-canopy/results/synthesis/new/" + country +"_"+ project + "_" + scan + ".csv"
        df.to_csv(name)
        
        
    except Exception as e:
        return f"Error processing {scan}: {e}"



keywords = ['bos001', 'bos002', 'bos003', 'bos004', 'gontrode', 'maeda', 'ber001', 'ber002', 'ber003', 'ber004', 'landshut']


# Create regex pattern to match any of the keywords
pattern = "|".join(keywords)

file_locs2 = file_locs[~file_locs["Full_path_x"].str.contains(pattern, case=False, na=False)]

start = time.time()
# Worker function to process each row
def process_row(row):
    rxp = row[0]
    rdb = row[1] 
    infos = rxp.split("/")
    country = infos[5]
    project = infos[6]
    scan = Path(rxp).stem
    try:
        get_plantprofiles(rxp, rdb, country, project, scan)
        return f"Processed: {scan}"
    except Exception as e:
        return f"Error processing {rxp}: {e}"
    
num_cores = os.cpu_count() // 2


results = []
with ThreadPoolExecutor(max_workers=num_cores) as executor:
    # Submit tasks to process each file
    futures = [executor.submit(process_row, (row.Full_path_x, row.Full_path_y)) for row in file_locs2.itertuples(index=False)]

    # Process results as they complete
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Files"):
        future.result()
end = time.time()
elapsed = (end - start)/60






start = time.time()
for i in range(file_locs.shape[0]):
    rxp = file_locs.iloc[i, 0]
    rdb = file_locs.iloc[i, 4]
    infos = rxp.split("/")
    country = infos[5]
    project = infos[6]
    try:
        get_plantprofiles(rxp, rdb, country, project, scan = Path(rxp).stem)
    except Exception as e:
        print("Error: {e}")
end = time.time()
elapsed = (end - start)/60


    

