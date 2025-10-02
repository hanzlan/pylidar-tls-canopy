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

start = timeit.timeit()


os.chdir(f'/Stor2/karun/data/')

cwd = os.getcwd()
scans = sorted(os.listdir(cwd+"/rxp/"))
scans_df = pd.DataFrame(scans)

scan_info = pd.concat([scans_df, pd.DataFrame(np.repeat("ScanPosVer.DAT", 38))], axis=1)

scan_info.columns = ["rxp_v", "dat_h"]

ignore_extensions = [".dat", ".DAT"]

file_data = [] 
for root, dirs, files in os.walk("."):
    for file in files:
        
        if not any(file.endswith(ext) for ext in ignore_extensions):
            file_data.append({"File": file, 
                              "Full_Path": os.path.join(root, file), 
                              "Directory": root,
                              "Scan": 
                              "Country" : })

file_data = pd.DataFrame(file_data)

def get_filepaths(data):
    

    pth = cwd+"/project.rdb/SCANS/"+data+"/SINGLESCANS/"
    
    dirs = os.listdir(pth)
    dirs = [i for i in dirs if "@" not in i]
    files_rdb = (glob.glob(os.path.join(pth, dirs[0],"*.rdbx")))
    
    
    pth = cwd+"/SCANS/"+data+"/SINGLESCANS/"
    files_rxp = glob.glob(os.path.join(pth,"*.rxp"))
    files_rxp = [i for i in files_rxp if "residual" not in i]
    files_rxp = [i for i in files_rxp if "@" not in i]

    
    pth = os.path.join(cwd,"Matrices")
    fname = data+".DAT"
    files_sop = glob.glob(os.path.join(pth, fname))
    
    return([files_rdb[0], files_rxp[0], files_sop[0]])
    #return(pd.DataFrame[files_rxp, files_rdb, files_sop])

'''
pth = cwd+"/project.rdb/SCANS/"+"ScanPos011"+"/SINGLESCANS/"
dirs = os.listdir(pth)
dirs = [i for i in dirs if "@" not in i]
files_rdb = (glob.glob(os.path.join(pth, dirs[0],"*.rdbx")))
    
pth = cwd+"/SCANS/"+"ScanPos010"+"/SINGLESCANS/"
files_rxp = glob.glob(os.path.join(pth,"*.rxp"))
files_rxp = [i for i in files_rxp if "residual" not in i]
files_rxp = [i for i in files_rxp if "@" not in i]


pth = os.path.join(cwd,"Matrices")
fname = data+".DAT"
files_sop = glob.glob(os.path.join(pth, fname))

"residual" in "/Stor2/karun/data/benchmarking/gontrode/vz400i/2024-03-04.002i.RiSCAN/SCANS/ScanPos011/SINGLESCANS/240304_131201.residual.rxp"
'''


paths_v = scans_df[0:round(scans_df.shape[0]/2)].map(get_filepaths)
paths_v = pd.DataFrame(paths_v.iloc[:,0].tolist(), columns = ["rdb_v", "rxp_v", "dat_v"])
paths_v = pd.concat([scans_df[0:round(scans_df.shape[0]/2)], paths_v], axis=1)

    
paths_h = scans_df[round(scans_df.shape[0]/2):scans_df.shape[0]].map(get_filepaths).reset_index(drop=True)
paths_h = pd.DataFrame(paths_h.iloc[:,0].tolist(), columns = ["rdb_h", "rxp_h", "dat_h"])
paths_h = pd.concat([scans_df[round(scans_df.shape[0]/2):scans_df.shape[0]].reset_index(drop=True), paths_h], axis=1)


paths = pd.concat([paths_v, paths_h], axis = 1)


scan_meta = pd.DataFrame(data = {'freq': [300, 300, 300, 600, 600, 600, 1200, 1200, 1200],
                                 'res' : [0.03, 0.04, 0.06, 0.03, 0.04, 0.06, 0.03, 0.04, 0.06]})

scan_meta = pd.DataFrame(data = {'freq': [300, 300, 300, 600, 600, 600, 600, 1200, 1200, 1200, 1200],
                                 'res' : [0.03, 0.04, 0.06, 0.02, 0.03, 0.04, 0.06, 0.02, 0.03, 0.04, 0.06]})

scan_meta = pd.DataFrame(data = {'freq': [300, 300, 300],
                                 'res' : [0.03, 0.04, 0.06]})

scan_meta = pd.DataFrame(data = {'freq': [100, 300, 600, 1200],
                                 'res' : [0.04, 0.04, 0.04, 0.04]})

scan_info = pd.concat([paths, scan_meta], axis =1)



scan_info.apply(lambda x : x.str.contains('@'), axis=1)
scan_info.apply(lambda x : x.str.contains('residual'), axis=1)
    

def get_plantprofiles(scans):

    
    #upright_rdbx_fn = scans['rdb_v']
    upright_rxp_fn = scans['rxp_v']
    upright_transform_fn = scans['dat_v']
    

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
        rdbx_file=None, method='WEIGHTED', min_zenith=35, max_zenith=70,
        query_str=query_str)
    
    vpp.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)
    
    
    hinge_pai = vpp.calcHingePlantProfiles()
    weighted_pai = vpp.calcSolidAnglePlantProfiles()
    linear_pai = vpp.calcLinearPlantProfiles()

    hinge_pavd = vpp.get_pavd(hinge_pai)
    linear_pavd = vpp.get_pavd(linear_pai)
    weighted_pavd = vpp.get_pavd(weighted_pai)
    
    
    
    points = riegl_rdb.readFile(scans["rdb_v"])
    points = ast.literal_eval(points[0]["riegl.scan_pattern"])
    res = round(points["rectangular"]["phi_increment"], 2)
    def roundup(x):
        return int(math.ceil(x / 100000.0)) * 100    
    freq = points["rectangular"]["program"]["name"]

    
    prof_dict = {"frequency":freq,
                 "resolution":res,
                 "hinge_pai":hinge_pai, 
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
    
    
    return prof_dict

bos4_vzi_test= scan_info.apply(get_plantprofiles, axis=1) 


scan_info['rdb_v'][6]


result = bos4_vzi_test
result = result.reset_index(drop=True)
for i in range(len(result)):
    df = pd.DataFrame(result[i])
    freq = result[i]['frequency']
    res = result[i]['resolution']
    name = "/home/kdayal/projects/pylidar-tls-canopy/results/bos4/new/" + "bos4_vzi_"+ str(freq) +"_"+ str(res) +".csv"
    df.to_csv(name)
    
    



temp = scan_info.iloc[0:1,]

res= scan_info.apply(get_plantprofiles, axis=1)

res3=temp.apply(get_plantprofiles, axis=1)

res3=scan_info.iloc[0:1,](get_plantprofiles, axis=1)

import pickle
with open('/home/1_projects/bos004.pkl', 'wb') as file:
    pickle.dump(res, file)

res = res3_vz_gon

val=0
fig, ax = plt.subplots()
plt.plot(res[0][val], label = "300,0.03")
plt.plot(res[1][val], label = "300,0.04")
plt.plot(res[2][val], label = "300,0.06")
plt.plot(res[3][val], label = "300,0.03")
plt.plot(res[4][val], label = "300,0.04")
plt.plot(res[5][val], label = "300,0.06")
plt.plot(res[6][val], label = "300,0.03")
plt.plot(res[7][val], label = "300,0.04")
plt.plot(res[8][val], label = "300,0.06")
plt.xlim(left=0, right=35)
plt.xlabel("PAD")
plt.ylabel("Height")
plt.legend()
plt.title("BOS004001")


val=3
fig, axs = plt.subplots(3)
plt.suptitle("BOS004001")
axs[0].plot([i/2 for i in range(100)], res[0][val],  label = "300,0.03")
axs[0].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[0].plot([i/2 for i in range(100)], res[2][val],  label = "300,0.06")
axs[0].plot([i/2 for i in range(100)], res[3][val],label = "600,0.03")
axs[0].plot([i/2 for i in range(100)], res[4][val], label = "600,0.04")
axs[0].plot([i/2 for i in range(100)], res[5][val], label = "600,0.06")
axs[0].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.03")
axs[0].plot([i/2 for i in range(100)], res[7][val], label = "1200,0.04")
axs[0].plot([i/2 for i in range(100)], res[8][val], label = "1200,0.06")
axs[0].set_title("Hinge PAD")
axs[0].set_xlim(xmin=1, xmax=30)
#axs[0].set_ylim(ymax=0.35)



val=4
axs[1].plot([i/2 for i in range(100)], res[0][val], label = "300,0.03")
axs[1].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[1].plot([i/2 for i in range(100)], res[2][val], label = "300,0.06")
axs[1].plot([i/2 for i in range(100)], res[3][val], label = "600,0.03")
axs[1].plot([i/2 for i in range(100)], res[4][val], label = "600,0.04")
axs[1].plot([i/2 for i in range(100)], res[5][val], label = "600,0.06")
axs[1].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.03")
axs[1].plot([i/2 for i in range(100)], res[7][val], label = "1200,0.04")
axs[1].plot([i/2 for i in range(100)], res[8][val], label = "1200,0.06")
axs[1].set_title("Weighted PAD")
axs[1].set_xlim(xmin=1, xmax=30)
#axs[1].set_ylim(ymax=0.35)



val=5
axs[2].plot([i/2 for i in range(100)], res[0][val], label = "300,0.03")
axs[2].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[2].plot([i/2 for i in range(100)], res[2][val], label = "300,0.06")
axs[2].plot([i/2 for i in range(100)], res[3][val], label = "600,0.03")
axs[2].plot([i/2 for i in range(100)], res[4][val], label = "600,0.04")
axs[2].plot([i/2 for i in range(100)], res[5][val], label = "600,0.06")
axs[2].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.03")
axs[2].plot([i/2 for i in range(100)], res[7][val], label = "1200,0.04")
axs[2].plot([i/2 for i in range(100)], res[8][val], label = "1200,0.06")
axs[2].set_title("Linear PAD")
axs[2].set_xlim(xmin=1, xmax=30)
#axs[2].set_ylim(ymax=0.35)


fig.supxlabel("Height")
fig.supylabel("PAD")

plt.legend()
plt.show()

names = ["300_0.03", "300_0.04", "300_0.06", "600_0.03", "600_0.04", "600_0.06", "1200_0.03", "1200_0.04", "1200_0.06"] 
profile =["hinge_pai", "weighted_pai", "linear_pai", "hinge_pavd", "linear_pavd", "weighted_pavd"] 

for i in range(9):
    for j in range(6):
        print(names[i], profile[j])
        fname = "~/1_projects/pylidar-tls-canopy/results/" + "BOS004LF002_" + names[i] + "_" + profile[j] + "_i" ".csv" 
        pd.DataFrame((res2[i][j])).to_csv(fname)


os.listdir("~/1_projects/pylidar-tls-canopy/results/")

os.getcwd("/home/")





val=3
fig, axs = plt.subplots(3)
axs[0].plot([i/2 for i in range(100)], res[0][val],  label = "300,0.03")
axs[0].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[0].plot([i/2 for i in range(100)], res[2][val],  label = "300,0.06")

axs[0].set_title("Hinge PAD")
#axs[0].set_xlim(xmin=1, xmax=15)
#axs[0].set_ylim(ymax=0.35)



val=4
axs[1].plot([i/2 for i in range(100)], res[0][val], label = "300,0.03")
axs[1].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[1].plot([i/2 for i in range(100)], res[2][val], label = "300,0.06")

axs[1].set_title("Weighted PAD")
#axs[1].set_xlim(xmin=1, xmax=15)
#axs[1].set_ylim(ymax=0.35)



val=5
axs[2].plot([i/2 for i in range(100)], res[0][val], label = "300,0.03")
axs[2].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[2].plot([i/2 for i in range(100)], res[2][val], label = "300,0.06")

axs[2].set_title("Linear PAD")
#axs[2].set_xlim(xmin=1, xmax=15)
#axs[2].set_ylim(ymax=0.35)


fig.supxlabel("Height")
fig.supylabel("PAD")

plt.legend()
plt.savefig("/home/kdayal/projects/pylidar-tls-canopy/results/gon3_vz.png", dpi=1200)




val=3
fig, axs = plt.subplots(3)
axs[0].plot([i/2 for i in range(100)], res[0][val],  label = "300,0.03")
axs[0].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[0].plot([i/2 for i in range(100)], res[2][val],  label = "300,0.06")
axs[0].plot([i/2 for i in range(100)], res[3][val],label = "600,0.02")
axs[0].plot([i/2 for i in range(100)], res[3][val],label = "600,0.03")
axs[0].plot([i/2 for i in range(100)], res[4][val], label = "600,0.04")
axs[0].plot([i/2 for i in range(100)], res[5][val], label = "600,0.06")
axs[0].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.02")
axs[0].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.03")
axs[0].plot([i/2 for i in range(100)], res[7][val], label = "1200,0.04")
axs[0].plot([i/2 for i in range(100)], res[8][val], label = "1200,0.06")
axs[0].set_title("Hinge PAD")
axs[0].set_xlim(xmin=0, xmax=40)
#axs[0].set_ylim(ymax=0.35)



val=4
axs[1].plot([i/2 for i in range(100)], res[0][val], label = "300,0.03")
axs[1].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[1].plot([i/2 for i in range(100)], res[2][val], label = "300,0.06")
axs[1].plot([i/2 for i in range(100)], res[3][val], label = "600,0.02")
axs[1].plot([i/2 for i in range(100)], res[3][val], label = "600,0.03")
axs[1].plot([i/2 for i in range(100)], res[4][val], label = "600,0.04")
axs[1].plot([i/2 for i in range(100)], res[5][val], label = "600,0.06")
axs[1].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.02")
axs[1].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.03")
axs[1].plot([i/2 for i in range(100)], res[7][val], label = "1200,0.04")
axs[1].plot([i/2 for i in range(100)], res[8][val], label = "1200,0.06")
axs[1].set_title("Weighted PAD")
axs[1].set_xlim(xmin=0, xmax=40)
#axs[1].set_ylim(ymax=0.35)



val=5
axs[2].plot([i/2 for i in range(100)], res[0][val], label = "300,0.03")
axs[2].plot([i/2 for i in range(100)], res[1][val], label = "300,0.04")
axs[2].plot([i/2 for i in range(100)], res[2][val], label = "300,0.06")
axs[2].plot([i/2 for i in range(100)], res[3][val], label = "600,0.02")
axs[2].plot([i/2 for i in range(100)], res[3][val], label = "600,0.03")
axs[2].plot([i/2 for i in range(100)], res[4][val], label = "600,0.04")
axs[2].plot([i/2 for i in range(100)], res[5][val], label = "600,0.06")
axs[2].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.02")
axs[2].plot([i/2 for i in range(100)], res[6][val], label = "1200,0.03")
axs[2].plot([i/2 for i in range(100)], res[7][val], label = "1200,0.04")
axs[2].plot([i/2 for i in range(100)], res[8][val], label = "1200,0.06")
axs[2].set_title("Linear PAD")
axs[2].set_xlim(xmin=0, xmax=40)
#axs[2].set_ylim(ymax=0.35)


fig.supxlabel("Height")
fig.supylabel("PAD")

plt.legend()
plt.show()

os.chdir(f"/home/projects/pylidar-tls-canopy/")
plt.savefig("/home/kdayal/projects/pylidar-tls-canopy/results/dummy_name3.png", dpi=1200)

types = ["hinge_pai", "weighted_pai", "linear_pai", "hinge_pavd", "linear_pavd", "weighted_pavd"]

for ind1 in range(3):
    for ind2 in range(6):        
        prof = pd.DataFrame(res2_vz_gon[ind1][ind2])
        name = "/home/kdayal/projects/pylidar-tls-canopy/results/gon2/" + "gon2_vz_"+ str(scan_meta['freq'][ind1]) +"_"+ str(scan_meta['res'][ind1]) +"_"+ types[ind2]+".csv"
        prof.to_csv(name)
            
