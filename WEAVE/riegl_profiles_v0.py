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
import re
from datetime import datetime
import json 
start = timeit.timeit()


paths = ['/Stor2/karun/data/benchmarking/bosland/003/D06/vz400i/new/2024-04-08-BOSLAND-3i.RiSCAN',
         '/Stor2/karun/data/benchmarking/bosland/003/H06/vz400i/new/2024-04-08-BOSLAND-4i.RiSCAN',
         '/Stor2/karun/data/benchmarking/bosland/004/B04/vz400i/new/2024-04-08-BOSLAND-2i.RiSCAN',
         '/Stor2/karun/data/benchmarking/bosland/004/H04/vz400i/new/2024-04-08-BOSLAND-1i.RiSCAN',
         '/Stor2/karun/data/benchmarking/berchtesgaden/002/F04/vz400i/new/2024-10-16-Eisgraben.RiSCAN',
         '/Stor2/karun/data/benchmarking/berchtesgaden/004/F05/vz400i/new/2024-09-04-Ofental.RiSCAN',
         '/Stor2/karun/data/benchmarking/australia/starvation/312/vz400i/new/2023-12-01_leaf_starCR_312.RiSCAN',
         '/Stor2/karun/data/benchmarking/australia/starvation/313/vz400i/new/2023-12-01_leaf_starCR_313.RiSCAN',
         '/Stor2/karun/data/benchmarking/australia/starvation/313/vz400i/new/2023-12-01_leaf_starCR_313.RiSCAN']




for fpath in paths[2:4]:
    print(fpath)
    
    os.chdir(fpath)
    print(fpath)
    cwd = os.getcwd()
    scans = sorted(os.listdir(cwd+"/SCANS"))
    scans_df = pd.DataFrame(scans)

    
    site = Path(fpath).parts[6]
    pos = Path(fpath).parts[7]

    #drop the last scan
    scans_df=scans_df[0:18]

    #drop any index
    scans_df=scans_df.reset_index(drop=True)


    def get_filepaths(data):
        
        

        pth = cwd+"/project.rdb/SCANS/"+ data+"/SINGLESCANS/"
        
        dirs = os.listdir(pth)
        print (dirs)
        # Checks to drop any other files
        dirs = [i for i in dirs if "@" not in i]
        
        # Convert to datetime objects and retain the mapping to original strings
        datetime_map = {date_str: datetime.strptime(date_str, '%y%m%d_%H%M%S') for date_str in dirs}

        # Find the most recent datetime
        most_recent_str = [max(datetime_map, key=datetime_map.get)]

        files_rdb = (glob.glob(os.path.join(pth, most_recent_str[0],"*.rdbx")))
        
        
        pth = cwd+"/SCANS/"+data+"/SINGLESCANS/"
        files_rxp = glob.glob(os.path.join(pth,"*.rxp"))
        files_rxp = [i for i in files_rxp if "residual" not in i]
        files_rxp = [i for i in files_rxp if "@" not in i]

        
        pth = os.path.join(cwd,"Matrices")
        fname = data+".DAT"
        files_sop = glob.glob(os.path.join(pth, fname))
        
        if os.path.splitext(os.path.basename(files_rdb[0]))[0] == os.path.splitext(os.path.basename(files_rxp[0]))[0]:
            return([files_rdb[0], files_rxp[0], files_sop[0]])
        
        #return(pd.DataFrame[files_rxp, files_rdb, files_sop])

    '''
    pth = cwd+"/project.rdb/SCANS/"+"ScanPos011"+"/SINGLESCANS/"
    dirs = os.listdir(pth)

    # Convert to datetime objects and retain the mapping to original strings
    datetime_map = {date_str: datetime.strptime(date_str, '%y%m%d_%H%M%S') for date_str in dirs}

    # Find the most recent datetime
    most_recent_str = [max(datetime_map, key=datetime_map.get)]

    # Checks to drop any other files
    dirs = [i for i in most_recent_str if "@" not in i]


    files_rdb = (glob.glob(os.path.join(pth, dirs[0],"*.rdbx")))
        
    pth = cwd+"/SCANS/"+"ScanPos011"+"/SINGLESCANS/"
    files_rxp = glob.glob(os.path.join(pth,"*.rxp"))
    # Checks to drop any other files
    files_rxp = [i for i in files_rxp if "residual" not in i]

    # Checks to drop any other files
    files_rxp = [i for i in files_rxp if "@" not in i]


    pth = os.path.join(cwd,"Matrices")
    fname = data+".DAT"
    files_sop = glob.glob(os.path.join(pth, fname))

    "residual" in "/Stor2/karun/data/benchmarking/gontrode/vz400i/2024-03-04.002i.RiSCAN/SCANS/ScanPos011/SINGLESCANS/240304_131201.residual.rxp"
    '''

    # Function to extract "ScanPos###"
    def extract_scan_position(path):
        match = re.search(r'/SCANS/(ScanPos\d+)/', path)
        return match.group(1) if match else None

    paths_v = scans_df[0:round(scans_df.shape[0]/2)].map(get_filepaths)
    paths_v = pd.DataFrame(paths_v.iloc[:,0].tolist(), columns = ["rdb_v", "rxp_v", "dat_v"])
    paths_v['scan_position'] = paths_v['rdb_v'].apply(extract_scan_position)

        
    paths_h = scans_df[round(scans_df.shape[0]/2):scans_df.shape[0]].map(get_filepaths).reset_index(drop=True)
    paths_h = pd.DataFrame(paths_h.iloc[:,0].tolist(), columns = ["rdb_h", "rxp_h", "dat_h"])
    paths_h['scan_position'] = paths_h['rdb_h'].apply(extract_scan_position)

    paths = pd.concat([paths_v, paths_h], axis = 1)


    # additional check whether some of the residual files are present
    paths.apply(lambda x : x.str.contains('@'), axis=1)
    paths.apply(lambda x : x.str.contains('residual'), axis=1)
        

    def get_plantprofiles(scans):

        
        upright_rdbx_fn = scans['rdb_v']
        upright_rxp_fn = scans['rxp_v']
        upright_transform_fn = scans['dat_v']
        

        tilt_rdbx_fn = scans['rdb_h']
        tilt_rxp_fn = scans['rxp_h']
        tilt_transform_fn = scans['dat_h']
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
        vpp.add_riegl_scan_position(upright_rxp_fn, upright_transform_fn, sensor_height=1.8,
            rdbx_file=upright_rdbx_fn, method='WEIGHTED', min_zenith=35, max_zenith=70,
            query_str=query_str)
        

        # If using RXP files only as input, set rdbx_file to None (the default)
        query_str = ['reflectance > -20']
        vpp.add_riegl_scan_position(tilt_rxp_fn, tilt_transform_fn, sensor_height=1.8,
            rdbx_file=tilt_rdbx_fn, method='WEIGHTED', min_zenith=5, max_zenith=35,
            query_str=query_str)
        
        vpp.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)
        
        hinge_idx = np.argmin(abs(vpp.zenith_bin - 57.5))
    
        pgap_phi_z = []
        for az in range(0, 360, vpp.ares):
            # Set invert to True if min_azimuth and max_azimuth specify the range to exclude
            vpp.get_pgap_theta_z(min_azimuth=az, max_azimuth=az+vpp.ares, invert=False)
            pgap_phi_z.append(vpp.pgap_theta_z[hinge_idx])
        
        
        hinge_pai = vpp.calcHingePlantProfiles()
        weighted_pai = vpp.calcSolidAnglePlantProfiles()
        linear_pai = vpp.calcLinearPlantProfiles()

        hinge_pavd = vpp.get_pavd(hinge_pai)
        linear_pavd = vpp.get_pavd(linear_pai)
        weighted_pavd = vpp.get_pavd(weighted_pai)
        
        
        pattern  = json.loads(riegl_rdb.readHeader(upright_rdbx_fn)['riegl.scan_pattern'])
        freq = pattern['rectangular']['program']['name']
        res = round(pattern['rectangular']['phi_increment'], 2)
        
        rdbf = os.path.split(upright_rdbx_fn)[1]
        rxpf = os.path.split(upright_rxp_fn)[1]

        
        prof_dict = {"scanrdb": rdbf,
                     "scanrxp": rxpf,
                    "frequency":freq,
                    "resolution":res,
                    "pgap45":pgap_phi_z[0],
                    "pgap135":pgap_phi_z[1],
                    "pgap225":pgap_phi_z[2],
                    "pgap315":pgap_phi_z[3],
                    "hinge_pai":hinge_pai, 
                    "weighted_pai":weighted_pai, 
                    "linear_pai":linear_pai, 
                    "hinge_pavd":hinge_pavd, 
                    "linear_pavd":linear_pavd, 
                    "weighted_pavd": weighted_pavd}
        

        print("done")
        print("***************************")

        #weighted_pai= pd.DataFrame(weighted_pai)
        #weighted_pai.to_csv(str(up)+'pai'+'.csv', sep=',', index=False, encoding='utf-8')

        #weighted_pavd= pd.DataFrame(weighted_pavd)
        #weighted_pavd.to_csv(str(up)+'pavd'+'.csv', sep=',', index=False, encoding='utf-8')
        
        
        return prof_dict
        

    test=paths.apply(get_plantprofiles, axis=1)




    result = test.reset_index(drop=True)



    for i in range(len(result)):
        df = pd.DataFrame(result[i])
        freq = result[i]['frequency']
        res = result[i]['resolution']
        scan = os.path.splitext(result[i]['scanrdb'])[0]
        name = "/home/kdayal/projects/pylidar-tls-canopy/results/benchmarking/bosland/" + site + "/" + pos + "/vz400i/"+ scan + "_vzi_"+ str(freq) +"_"+ str(res) +".csv"
        df.to_csv(name)
        print(freq)
    
