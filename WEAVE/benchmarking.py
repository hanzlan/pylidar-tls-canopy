
import numpy as np

import os


import glob

import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.ticker import MaxNLocator

from pylidar_tls_canopy import riegl_io, plant_profile, plant_profile_2, grid




from os import walk

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

projpaths = ['/Stor2/karun/data/benchmarking/reprocessed/australia/screek/312/VZ400i/2023-12-01_leaf_starCR_312.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/australia/screek/313/VZ400i/2023-12-01_leaf_starCR_313.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/australia/screek/314/VZ400i/2023-12-01_leaf_starCR_314.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/bosland/003/D06/VZ400/2024-04-08.003.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/bosland/004/B04/VZ400/2024-04-08.002.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/bosland/004/H04/VZ400/2024-04-08.001.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/bosland/003/D06/VZ400i/2024-04-08-BOSLAND-3i.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/bosland/003/H06/VZ400i/2024-04-08-BOSLAND-4i.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/bosland/004/B04/VZ400i/2024-04-08-BOSLAND-2i.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/bosland/004/H04/VZ400i/2024-04-08-BOSLAND-1i.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/gontrode/transect/01/VZ400/2024-03-04.001.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/gontrode/transect/02/VZ400/2024-03-04.002.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/gontrode/transect/03/VZ400/2024-03-04.003.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/gontrode/transect/01/VZ400i/2024-03-04.001i.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/gontrode/transect/02/VZ400i/2024-03-04.002i.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/gontrode/transect/03/VZ400i/2024-03-04.003i.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/germany/002/F04/VZ400i/2024-10-16-Eisgraben.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/germany/004/F05/VZ400i/2024-09-04-Ofental.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/germany/gfz/01/pos1.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/germany/gfz/02/pos2.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/germany/gfz/03/pos3.RiSCAN']


projpaths = ['/Stor2/karun/data/benchmarking/reprocessed/australia/screek/312/VZ400i/2023-12-01_leaf_starCR_312.RiSCAN',
             '/Stor2/karun/data/benchmarking/reprocessed/germany/gfz/03/pos3.RiSCAN']



def getpaths(projscan):
    
    locs = os.listdir(os.path.join(projpath, 'project.rdb', 'SCANS', projscan, "SINGLESCANS"))
    locs = [x for x in locs if "@" not in x]
    if len(locs) > 0:
        if len(locs) > 1:
            selected_loc = max(locs)
        else:
            selected_loc = locs[0]
        rdbpath = os.listdir(os.path.join(projpath, 'project.rdb', 'SCANS', projscan, "SINGLESCANS", selected_loc))
        rdbpath = [x for x in rdbpath if x.endswith('.rdbx')]
        rxpname = os.path.splitext(rdbpath[0])[0]+ ".rxp"
        for root, dirs, files in os.walk(os.path.join(projpath, "SCANS")):
            if rxpname in files:
                rxpath = os.path.join(root, rxpname)
        rdbpath = os.path.join(projpath, 'project.rdb', 'SCANS', projscan, "SINGLESCANS", str(selected_loc), str(rdbpath[0]))
        sopname = projscan+".DAT"
        
        matrices_path = os.path.join(projpath,"Matrices")

        
        if not os.path.isdir(matrices_path) or not os.listdir(matrices_path):
            print(f"No files found in: {matrices_path}")
            return 
        
        for root, dirs, files in os.walk(matrices_path):
            if sopname in files:
                sopath = os.path.join(root, sopname)
        return [rdbpath, rxpath, sopath]
    return ["none", "none", "none"]


all_path_tables = []  # will store one DataFrame per project

# for benchmarking data that has all vertical scans first and then all tilt scans
for projpath in projpaths:
    try:
        scan_root = os.path.join(projpath, 'project.rdb', 'SCANS')
        if not os.path.exists(scan_root):
            continue

        projscanpos = sorted(os.listdir(scan_root))

        paths = list(map(getpaths, projscanpos))
        paths = pd.DataFrame(paths)

        # Split into vertical and horizontal
        split = len(paths) // 2
        paths_v = paths.iloc[:split].reset_index(drop=True)
        paths_v.columns = ["rdb_v", "rxp_v", "dat_v"]

        paths_h = paths.iloc[split:].reset_index(drop=True)
        paths_h.columns = ["rdb_h", "rxp_h", "dat_h"]

        paths_combined = pd.concat([paths_v, paths_h], axis=1)
        paths_combined["project_path"] = os.path.basename(projpath)  # optional: add project identifier

        all_path_tables.append(paths_combined)
    except Exception as e:
        print(projpath)
        break


# for standard TLS acquisition with alternating vertical and tilt scans
for projpath in projpaths:
    try:
        scan_root = os.path.join(projpath, 'project.rdb', 'SCANS')
        if not os.path.isdir(scan_root):
            continue

        # 1) List scans in a stable order (adjust if you need natural sort)
        scans = sorted(os.listdir(scan_root))

        # 2) Collect paths per scan (uses your existing getpaths(projscan) that relies on global projpath)
        rows = [getpaths(s) for s in scans]  # returns [rdb, rxp, dat]
        df = pd.DataFrame(rows, columns=["rdb", "rxp", "dat"])
        df["scan"] = scans

        # 3) Pair consecutive scans: (0,1) -> V/H, (2,3) -> V/H, ...
        paired = []
        for i in range(0, len(df), 2):
            v = df.iloc[i]
            if i + 1 < len(df):
                h = df.iloc[i + 1]
            else:
                # odd count: last vertical without a tilt partner
                h = pd.Series({"rdb": "none", "rxp": "none", "dat": "none", "scan": None})

            paired.append({
                "rdb_v": v["rdb"], "rxp_v": v["rxp"], "dat_v": v["dat"], "scan_v": v["scan"],
                "rdb_h": h["rdb"], "rxp_h": h["rxp"], "dat_h": h["dat"], "scan_h": h["scan"],
            })
        paths_combined = pd.DataFrame(paired)
        paths_combined["project_path"] = os.path.basename(projpath)

        all_path_tables.append(paths_combined)

        # Optional: flag odd counts so you notice unpaired last items
        if len(df) % 2 == 1:
            print(f"[warn] Odd number of scans in {projpath}: last vertical has no tilt pair.")

    except Exception as e:
        print(f"[error] {projpath}: {e}")
        break
    

# Combine all into one big table
all_paths_df = pd.concat(all_path_tables, ignore_index=True)

all_paths_df.groupby('project_path').size().reset_index(name='count')

# doublecheck that all files are linkedcorrectly
 
# Compare filenames (not full paths) in vertical paths
all_paths_df['v_match'] = all_paths_df.apply(lambda row: os.path.basename(row['rdb_v']).replace('.rdbx', '') == os.path.basename(row['rxp_v']).replace('.rxp', ''), axis=1)

# Compare filenames in horizontal paths
all_paths_df['h_match'] = all_paths_df.apply(lambda row: os.path.basename(row['rdb_h']).replace('.rdbx', '') == os.path.basename(row['rxp_h']).replace('.rxp', ''), axis=1)


def extract_scanpos(path):
    match = re.search(r'ScanPos\d{3}', path)
    return match.group(0) if match else None

# Apply to each row to check ScanPos consistency
all_paths_df['v_scanpos_match'] = all_paths_df.apply(
    lambda row: len(set([
        extract_scanpos(row['rdb_v']),
        extract_scanpos(row['rxp_v']),
        extract_scanpos(row['dat_v'])
    ])) == 1, axis=1)

all_paths_df['h_scanpos_match'] = all_paths_df.apply(
    lambda row: len(set([
        extract_scanpos(row['rdb_h']),
        extract_scanpos(row['rxp_h']),
        extract_scanpos(row['dat_h'])
    ])) == 1, axis=1
)

all_paths_df[['v_match', 'v_scanpos_match', 'h_match', 'h_scanpos_match']].all().all()

def get_scanparams(scans):
    upright_rdbx_fn = scans['rdb_v']
    upright_rxp_fn = scans['rxp_v']
    upright_transform_fn = scans['dat_v']
    

    tilt_rdbx_fn = scans['rdb_h']
    tilt_rxp_fn = scans['rxp_h']
    tilt_transform_fn = scans['dat_h']
    
    
    pattern_v  = json.loads(riegl_rdb.readHeader(upright_rdbx_fn)['riegl.scan_pattern'])
    freq_v = pattern_v['rectangular']['program']['name']
    res_v = round(pattern_v['rectangular']['phi_increment'], 2)
    
    
    pattern_h  = json.loads(riegl_rdb.readHeader(tilt_rdbx_fn)['riegl.scan_pattern'])
    freq_h = pattern_h['rectangular']['program']['name']
    res_h = round(pattern_h['rectangular']['phi_increment'], 2)
    
    if freq_v==freq_h and res_v==res_h:
        return res_v, re.sub(r'\D', '', freq_v)
    else:
        return None, None

def get_scanparams(row):
    try:
        # Read patterns
        pat_v = json.loads(riegl_rdb.readHeader(row['rdb_v'])['riegl.scan_pattern'])
        pat_h = json.loads(riegl_rdb.readHeader(row['rdb_h'])['riegl.scan_pattern'])

        # Extract numeric frequency from names (e.g., "300kHz", "PRG_300kHz")
        def parse_freq(name):
            if name is None:
                return np.nan
            m = re.search(r'(\d+)\s*k?hz', str(name), flags=re.I)
            return float(m.group(1)) if m else float(re.sub(r'\D', '', str(name)) or np.nan)

        f_v = parse_freq(pat_v.get('rectangular', {}).get('program', {}).get('name'))
        f_h = parse_freq(pat_h.get('rectangular', {}).get('program', {}).get('name'))

        # Extract angular resolution (phi_increment)
        def parse_res(pat):
            x = pat.get('rectangular', {}).get('phi_increment')
            return round(float(x), 2) if x is not None else np.nan

        r_v = parse_res(pat_v)
        r_h = parse_res(pat_h)

        # If upright & tilt disagree, mark NA so you can filter later
        if (pd.isna(f_v) or pd.isna(f_h) or pd.isna(r_v) or pd.isna(r_h) or
            (f_v != f_h) or (r_v != r_h)):
            return (np.nan, np.nan)

        return (r_v, f_v)

    except Exception:
        # Any error → return NaNs but DO NOT raise
        return (np.nan, np.nan)

all_paths_df[['resolution', 'frequency']] = all_paths_df.apply(get_scanparams, axis=1, result_type='expand')

# We are ensuring that only one plane per plot is used, which is derived from the 0.03° resolution 300kHz data. It does not make sense to create a new plane for each scan when the location is the same. 
def get_planeparams(scans):
    
    # Sort by resolution and frequency ascending → lowest values first
    min_row = scans.sort_values(['resolution', 'frequency'], ascending=[True, True]).iloc[0]

    
    upright_rdbx_fn = min_row['rdb_v']
    upright_rxp_fn = min_row['rxp_v']
    upright_transform_fn = min_row['dat_v']
    

    tilt_rdbx_fn = min_row['rdb_h']
    tilt_rxp_fn = min_row['rxp_h']
    tilt_transform_fn = min_row['dat_h']

    
    
    # Determine the origin coordinates to use
    transform_matrix = riegl_io.read_transform_file(upright_transform_fn)
    x0,y0,z0,_ = transform_matrix[3,:]

    grid_extent = 60
    grid_resolution = 1
    grid_origin = [x0,y0]
    # If using RXP files only as input, set rxp to True:
    x,y,z,r = plant_profile_2.get_min_z_grid([upright_rdbx_fn, tilt_rdbx_fn],
                                           [upright_transform_fn, tilt_transform_fn],
                                           grid_extent, grid_resolution, 
                                           grid_origin=grid_origin,
                                           rxp=False)

    
    # Optional weighting of points by 1 / range
    planefit = plant_profile_2.plane_fit_hubers(x, y, z, w=1/r)
    scans['parameter_a'] = planefit['Parameters'][1]
    scans['parameter_b'] = planefit['Parameters'][2]
    scans['parameter_c'] = planefit['Parameters'][0]
    return scans

all_paths_df = all_paths_df.dropna(subset=['resolution', 'frequency']).reset_index(drop=True)


all_paths_df = all_paths_df.groupby('project_path', group_keys=False).apply(get_planeparams)
all_paths_df1 = pd.read_csv("/home/kdayal/projects/pylidar-tls-canopy/all_paths_df.csv")
df = pd.concat([all_paths_df, all_paths_df1], axis=0, ignore_index=True)
all_paths_df.to_csv("all_paths_df_new.csv", index=False)


import pandas as pd
from IPython.display import display  # optional, for nicer output

all_paths_df = pd.read_csv("/home/kdayal/projects/pylidar-tls-canopy/all_paths_df_new.csv")
display(all_paths_df)  # or just use all_paths_df



def get_plantprofiles(scans):

    project = scans['project_path']
    
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
    
    # If the ground plane is not defined then set ground_plane to None
    # and use the sensor_height argument when adding scan positions
    terrain_params = np.array([scans['parameter_c'], scans['parameter_a'], scans['parameter_b']])
    print(terrain_params)
    vpp = plant_profile_2.Jupp2009(hres=0.5, 
                                    zres=5, 
                                    ares=360,
                                    min_z=5, 
                                    max_z=70, 
                                    min_h=0, 
                                    max_h=50,
                                    ground_plane=terrain_params)

    # If using RXP files only as input, set rdbx_file to None (the default)
    query_str = ['reflectance > -20']
    vpp.add_riegl_scan_position(upright_rxp_fn, 
                                upright_transform_fn, 
                                sensor_height=None,
                                rdbx_file=upright_rdbx_fn, 
                                method='WEIGHTED', 
                                min_zenith=35, 
                                max_zenith=70,
                                query_str=query_str)
    

    # If using RXP files only as input, set rdbx_file to None (the default)
    query_str = ['reflectance > -20']
    vpp.add_riegl_scan_position(tilt_rxp_fn, 
                                tilt_transform_fn, 
                                sensor_height=None,
                                rdbx_file=tilt_rdbx_fn, 
                                method='WEIGHTED', 
                                min_zenith=5, 
                                max_zenith=35,
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
    
    vrdbf = os.path.split(upright_rdbx_fn)[1]
    vrxpf = os.path.split(upright_rxp_fn)[1]
    hrdbf = os.path.split(tilt_rdbx_fn)[1]
    hrxpf = os.path.split(tilt_rxp_fn)[1]

    
    prof_dict = {"projpath":project,
                "scanvrdb": vrdbf,
                "scanvrxp": vrxpf,
                "scanhrdb": hrdbf,
                "scanhrxp": hrxpf,
                "frequency":freq,
                "resolution":res,
                "pgap":pgap_phi_z[0],
                "hinge_pai":hinge_pai, 
                "weighted_pai":weighted_pai, 
                "linear_pai":linear_pai, 
                "hinge_pavd":hinge_pavd, 
                "linear_pavd":linear_pavd, 
                "weighted_pavd": weighted_pavd}
    
    df = pd.DataFrame(prof_dict)
    df.to_csv(f"reprocessed_new_{vrdbf}.csv", index=False)
    
    print("done")
    print("***************************")
    
    

    return prof_dict



xx = all_paths_df[0:1]
        
test = all_paths_df.apply(get_plantprofiles, axis=1)       




from pandas import json_normalize

# test is your list of dictionaries
dfs = [pd.DataFrame(d) for d in test]
df = pd.concat(dfs, ignore_index=True)
df.to_csv("reprocessed_allber_vzi.csv", index=False)   



all_paths_df['project_path']



all_paths_df = pd.read_csv("/home/kdayal/projects/pylidar-tls-canopy/all_paths_df.csv")


## examining the data for differences in vz400 and vz400i


vz = all_paths_df.loc[(all_paths_df['project_path'] == '2024-04-08.001.RiSCAN') & 
                 (all_paths_df['resolution'] == 0.03)]

vzi = all_paths_df.loc[(all_paths_df['project_path'] == '2024-04-08-BOSLAND-1i.RiSCAN') & 
                 (all_paths_df['resolution'] == 0.03) &
                 (all_paths_df['frequency'] == 300)]


scans = vz


upright_rdbx_fn = scans['rdb_v'].iloc[0]
upright_rxp_fn = scans['rxp_v'].iloc[0]
upright_transform_fn = scans['dat_v'].iloc[0]


tilt_rdbx_fn = scans['rdb_h'].iloc[0]
tilt_rxp_fn = scans['rxp_h'].iloc[0]
tilt_transform_fn = scans['dat_h'].iloc[0]



# Determine the origin coordinates to use
transform_matrix = riegl_io.read_transform_file(upright_transform_fn)
x0,y0,z0,_ = transform_matrix[3,:]

grid_extent = 60
grid_resolution = 1
grid_origin = [x0,y0]

# If the ground plane is not defined then set ground_plane to None
# and use the sensor_height argument when adding scan positions
terrain_params = np.array([scans['parameter_c'].iloc[0], scans['parameter_a'].iloc[0], scans['parameter_b'].iloc[0]])
print(terrain_params)
vpp = plant_profile.Jupp2009(hres=0.5, 
                            zres=5, 
                            ares=90,
                            min_z=35, 
                            max_z=70, 
                            min_h=0, 
                            max_h=50,
                            ground_plane=terrain_params)

min_zenith_r = np.radians(35)
max_zenith_r = np.radians(70)
pulse_cols = ['zenith','azimuth','target_count']
point_cols = ['x','y','z','range','target_index',
                'zenith','azimuth','target_count']


pulses = {}
with riegl_io.RXPFile(rxp_file, transform_file=transform_file, query_str=query_str) as rxp:
    for col in pulse_cols:
        pulses[col] = rxp.get_data(col, return_as_point_attribute=False)
    idx = (pulses['zenith'] >= min_zenith_r) & (pulses['zenith'] < max_zenith_r)
    if np.any(idx):
        self.add_shots(pulses['target_count'][idx], pulses['zenith'][idx],
            pulses['azimuth'][idx], method=method)

    points = {}
    if rdbx_file:
        with riegl_io.RDBFile(rdbx_file, transform_file=transform_file, query_str=query_str) as f:
            for col in point_cols:
                points[col] = f.get_data(col)
    else:
        for col in point_cols:
            points[col] = rxp.get_data(col, return_as_point_attribute=True)

    if self.ground_plane is None:
        if sensor_height is not None:
            zoffset = rxp.transform[3,2] - sensor_height
        else:
            zoffset = rxp.transform[3,2]
    else:
        zoffset = self.ground_plane[0]

if self.ground_plane is None:
    height = points['z'] + zoffset
else: 
    height = points['z'] - (self.ground_plane[1] * points['x'] +
        self.ground_plane[2] * points['y'] + zoffset)

idx = (points['zenith'] >= min_zenith_r) & (points['zenith'] < max_zenith_r)
if max_hr is not None:
    hr = points['range'] * np.sin(points['zenith'])
    idx &= hr < max_hr
if np.any(idx):
    self.add_targets(height[idx], points['target_index'][idx], 
        points['target_count'][idx], points['zenith'][idx],
        points['azimuth'][idx], method=method)







def add_riegl_scan_position(self, rxp_file, transform_file, rdbx_file=None, sensor_height=None,
        method='WEIGHTED', min_zenith=5, max_zenith=70, max_hr=None, query_str=None):
        """
        Add a RIEGL scan position to the profile
        """
        min_zenith_r = np.radians(min_zenith)
        max_zenith_r = np.radians(max_zenith)
        pulse_cols = ['zenith','azimuth','target_count']
        point_cols = ['x','y','z','range','target_index',
                      'zenith','azimuth','target_count']

        pulses = {}
        with riegl_io.RXPFile(rxp_file, transform_file=transform_file, query_str=query_str) as rxp:
            for col in pulse_cols:
                pulses[col] = rxp.get_data(col, return_as_point_attribute=False)
            idx = (pulses['zenith'] >= min_zenith_r) & (pulses['zenith'] < max_zenith_r)
            if np.any(idx):
                self.add_shots(pulses['target_count'][idx], pulses['zenith'][idx],
                    pulses['azimuth'][idx], method=method)

            points = {}
            if rdbx_file:
                with riegl_io.RDBFile(rdbx_file, transform_file=transform_file, query_str=query_str) as f:
                    for col in point_cols:
                        points[col] = f.get_data(col)
            else:
                for col in point_cols:
                    points[col] = rxp.get_data(col, return_as_point_attribute=True)

            if self.ground_plane is None:
                if sensor_height is not None:
                    zoffset = rxp.transform[3,2] - sensor_height
                else:
                    zoffset = rxp.transform[3,2]
            else:
                zoffset = self.ground_plane[0]
       
        if self.ground_plane is None:
            height = points['z'] + zoffset
        else: 
            height = points['z'] - (self.ground_plane[1] * points['x'] +
                self.ground_plane[2] * points['y'] + zoffset)
        
        idx = (points['zenith'] >= min_zenith_r) & (points['zenith'] < max_zenith_r)
        if max_hr is not None:
            hr = points['range'] * np.sin(points['zenith'])
            idx &= hr < max_hr
        if np.any(idx):
            self.add_targets(height[idx], points['target_index'][idx], 
                points['target_count'][idx], points['zenith'][idx],
                points['azimuth'][idx], method=method)




vpp_vz = plant_profile.Jupp2009(hres=0.5, 
                                zres=5, 
                                ares=90,
                                min_z=35, 
                                max_z=70, 
                                min_h=0, 
                                max_h=50,
                                ground_plane=terrain_params)


# If using RXP files only as input, set rdbx_file to None (the default)
query_str = ['reflectance > -20']
vpp_vz.add_riegl_scan_position(upright_rxp_fn, 
                            upright_transform_fn, 
                            sensor_height=None,
                            rdbx_file=upright_rdbx_fn, 
                            method='WEIGHTED', 
                            min_zenith=35, 
                            max_zenith=70,
                            query_str=query_str)

vpp_vz.add_riegl_scan_position(tilt_rxp_fn, 
                            tilt_transform_fn, 
                            sensor_height=None,
                            rdbx_file=tilt_rdbx_fn, 
                            method='WEIGHTED', 
                            min_zenith=35, 
                            max_zenith=70,
                            query_str=query_str)

vpp_vz.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)

hinge_pai_vz = vpp_vz.calcHingePlantProfiles()
linear_pai_vz = vpp_vz.calcLinearPlantProfiles()
weighted_pai_vz = vpp_vz.calcSolidAnglePlantProfiles()

hinge_pavd_vz = vpp_vz.get_pavd(hinge_pai_vz)
linear_pavd_vz = vpp_vz.get_pavd(linear_pai_vz)
weighted_pavd_vz = vpp_vz.get_pavd(weighted_pai_vz)

scans = vzi


upright_rdbx_fn = scans['rdb_v'].iloc[0]
uptight_rxp_fn = scans['rxp_v'].iloc[0]
upright_transform_fn = scans['dat_v'].iloc[0]


tilt_rdbx_fn = scans['rdb_h'].iloc[0]
tilt_rxp_fn = scans['rxp_h'].iloc[0]
tilt_transform_fn = scans['dat_h'].iloc[0]


vpp_vzi = plant_profile.Jupp2009(hres=0.5, 
                                zres=5, 
                                ares=90,
                                min_z=35, 
                                max_z=70, 
                                min_h=0, 
                                max_h=50,
                                ground_plane=terrain_params)


# If using RXP files only as input, set rdbx_file to None (the default)
query_str = ['reflectance > -20']
vpp_vzi.add_riegl_scan_position(upright_rxp_fn, 
                            upright_transform_fn, 
                            sensor_height=None,
                            rdbx_file=upright_rdbx_fn, 
                            method='WEIGHTED', 
                            min_zenith=35, 
                            max_zenith=70,
                            query_str=query_str)

vpp_vzi.add_riegl_scan_position(tilt_rxp_fn, 
                            tilt_transform_fn, 
                            sensor_height=None,
                            rdbx_file=tilt_rdbx_fn, 
                            method='WEIGHTED', 
                            min_zenith=5, 
                            max_zenith=35,
                            query_str=query_str)

vpp_vzi.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)


hinge_pai_vzi = vpp_vzi.calcHingePlantProfiles()
linear_pai_vzi = vpp_vzi.calcLinearPlantProfiles()
weighted_pai_vzi = vpp_vzi.calcSolidAnglePlantProfiles()

hinge_pavd_vzi = vpp_vzi.get_pavd(hinge_pai_vzi)
linear_pavd_vzi = vpp_vzi.get_pavd(linear_pai_vzi)
weighted_pavd_vzi = vpp_vzi.get_pavd(weighted_pai_vzi)

import numpy as np
import matplotlib.pyplot as plt

z = np.arange(0, 101)  # height in meters

fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

# Panel 1 – Hinge
axes[0].plot(hinge_pai_vz, z, label='vz', linestyle='-')
axes[0].plot(hinge_pai_vzi, z, label='vzi', linestyle='--')
axes[0].set_title('Hinge PAI')
axes[0].invert_yaxis()
axes[0].set_ylabel('Height (m)')
axes[0].set_xlabel('PAI')
axes[0].legend()

# Panel 2 – Linear
axes[1].plot(linear_pai_vz, z, label='vz', linestyle='-')
axes[1].plot(linear_pai_vzi, z, label='vzi', linestyle='--')
axes[1].set_title('Linear PAI')
axes[1].set_xlabel('PAI')

# Panel 3 – Weighted
axes[2].plot(weighted_pai_vz, z, label='vz', linestyle='-')
axes[2].plot(weighted_pai_vzi, z, label='vzi', linestyle='--')
axes[2].set_title('Weighted PAI')
axes[2].set_xlabel('PAI')

plt.tight_layout()
plt.savefig("pai_comparison.png", dpi=300, bbox_inches='tight')



import numpy as np
import matplotlib.pyplot as plt

z = np.arange(0, 100)  # Height in meters

plt.figure(figsize=(5, 6))
plt.plot(weighted_pavd_vz, z, label='vz', linestyle='-')
plt.plot(weighted_pavd_vzi, z, label='vzi', linestyle='--')

plt.xlabel('PAVD')
plt.ylabel('Height (m)')
plt.title('Weighted PAVD Profile')
plt.legend()
plt.grid(True)


plt.savefig("weighted_pavd_comparison.png", dpi=300)



plt.figure(figsize=(5, 5))
plt.scatter(weighted_pavd_vz, weighted_pavd_vzi, s=10, alpha=0.7)

plt.xlabel('VZ')
plt.ylabel('VZI')
plt.title('Scatter Plot: VZ vs VZI (Weighted PAVD)')
plt.grid(True)
plt.axis('equal')  # Equal scaling for both axes
plt.tight_layout()
plt.savefig("scatter_vz_vzi.png", dpi=300)
plt.show()