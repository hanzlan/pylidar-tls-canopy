#!/usr/bin/env python3
"""
pylidar_tls_canopy

Drivers for handling LEAF files

John Armston
University of Maryland
December 2022
"""

import sys
import re
import os
import ast
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


class LeafScanFile:
    def __init__(self, filename, sensor_height=None, transform=True, 
        max_range=120, zenith_offset=0):
        self.filename = filename
        self.sensor_height = sensor_height
        self.transform = transform
        self.max_range = max_range
        self.zenith_offset = zenith_offset
        
        pattern = re.compile(r'(\w{8})_(\d{4})_(hemi|hinge|ground)_(\d{8})-(\d{6})Z_(\d{4})_(\d{4})\.csv')
        fileinfo = pattern.fullmatch( os.path.basename(filename) )
        if fileinfo:
            self.serial_number = fileinfo[1]
            self.scan_count = int(fileinfo[2])
            self.scan_type = fileinfo[3]
            self.datetime = datetime.strptime(f'{fileinfo[4]}{fileinfo[5]}', '%Y%m%d%H%M%S')
            self.zenith_shots = int(fileinfo[6])
            self.azimuth_shots = int(fileinfo[7])
        else:
            print(f'{filename} is not a recognized LEAF scan file')
        
        self.read_meta()
        self.read_data()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def read_meta(self):
        """
        Read the file header
        """
        with open(self.filename, 'r') as f:
            self.header = {}
            self.footer = {}
            in_header = True
            for line in f:
                if line.startswith('#'):
                    if 'Finished' in line:
                        lparts = line.strip().split()
                        self.duration = float(lparts[2])
                    elif 'GPS' in line:
                        lparts = line[4::].strip().split(',')
                        self.gps = lparts
                    else:
                        lparts = line.strip().split(':')
                        key = lparts[0][1::].strip()
                        if key in ('Batt','Curr','Lidar Temp','Motor Temp',
                            'Encl. Temp','Encl. humidity'):
                            val = lparts[1].strip().split()[0]
                        else:
                            val = lparts[1].strip()
                        try:
                            val = ast.literal_eval(val)
                        except:
                            pass
                        if in_header:
                            self.header[key] = val
                        else:
                            self.footer[key] = val
                else:
                    in_header = False

    def read_data(self):
        """
        Read file
        """
        if self.header['Firmware ver.'] >= 4.11:
            scan_nsteps = 2.56e4
            dtypes = {'sample_count':int, 'scan_encoder':float, 'rotary_encoder':float,
                'range1':float, 'intensity1':int, 'range2':float, 'intensity2':int, 
                'sample_time':float}
        else:
            scan_nsteps = 1e4
            dtypes = {'sample_count':int, 'scan_encoder':float, 'rotary_encoder':float,
                'range1':float, 'intensity1':int, 'range2':float, 'sample_time':float}

        self.data = pd.read_csv(self.filename, comment='#', na_values=-1.0,
            names=dtypes.keys(), on_bad_lines='warn')

        if self.data.empty:
            return

        # Remove truncated records 
        num_short_lines = self.data.shape[0] - self.data['sample_time'].count()
        if num_short_lines > 0:
            idx = self.data['sample_time'].notna()
            self.data = self.data.loc[idx]
            self.data = self.data.astype(dtypes)
            msg = f'Removed {num_short_lines:d} truncated records in {self.filename}'
            print(msg)
        
        # Set invalid values to NaN
        for n in (1,2):
            mask = (self.data[f'range{n:d}'] > self.max_range)
            if f'intensity{n:d}' in self.data.columns:
                mask |= (self.data[f'intensity{n:d}'] <= 0)
            self.data.loc[mask,f'range{n:d}'] = np.nan

        self.data['target_count'] = (2 - self.data['range1'].isna().astype(int) +
            self.data['range2'].isna().astype(int))

        self.data['datetime'] = [self.datetime + timedelta(milliseconds=s)
            for s in self.data['sample_time'].cumsum()]

        self.data['zenith'] = self.data['scan_encoder'] / scan_nsteps * 2 * np.pi + self.zenith_offset
        self.data['azimuth'] = self.data['rotary_encoder'] / 2e4 * 2 * np.pi

        if self.transform:
            dx,dy,dz = (d / 1024 for d in self.header['Tilt'])
            r,theta,phi = xyz2rza(dx, dy, dz)
            self.data['zenith'] += theta
            self.data['azimuth'] += phi

        if self.scan_type == 'hemi':
            idx = self.data['zenith'] < np.pi 
            self.data.loc[idx,'azimuth'] = self.data.loc[idx,'azimuth'] + np.pi
        idx = self.data['azimuth'] > (2 * np.pi)
        self.data.loc[idx,'azimuth'] = self.data.loc[idx,'azimuth'] - (2 * np.pi)
        idx = self.data['azimuth'] < 0
        self.data.loc[idx,'azimuth'] = self.data.loc[idx,'azimuth'] + (2 * np.pi)
        self.data['zenith'] = (self.data['zenith'] - np.pi).abs()

        for n,name in enumerate(['range1','range2'], start=1):
            x,y,z = rza2xyz(self.data[name], self.data['zenith'], self.data['azimuth'])
            self.data[f'x{n:d}'] = x
            self.data[f'y{n:d}'] = y
            self.data[f'z{n:d}'] = z
            if self.sensor_height:
                self.data[f'h{n:d}'] = z + self.sensor_height


class LeafPowerFile:
    def __init__(self, filename):
        self.filename = filename
        pattern = re.compile(r'(\w{8})_pwr_(\d{8})\.csv')
        fileinfo = pattern.fullmatch( os.path.basename(filename) )
        if fileinfo:
            self.serial_number = fileinfo[1]
            self.datetime = datetime.strptime(fileinfo[2], '%Y%m%d')
        else:
            print(f'{filename} is not a recognized LEAF power file')
        self.read_data()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def read_data(self):
        """
        Read file
        """
        self.data = pd.read_csv(self.filename, on_bad_lines='warn',
            names=['datetime','battery_voltage','current',
                   'temperature','humidity'])

        num_short_lines = self.data.shape[0] - self.data['humidity'].count()
        if num_short_lines > 0:
            idx = self.data['humidity'].notna()
            self.data = self.data.loc[idx]
            msg = f'{num_short_lines:d} truncated records were ignored in {self.filename}'
            print(msg)

        self.data['datetime'] = pd.to_datetime(self.data['datetime'],
            format='%Y%m%d-%H%M%S')


def rza2xyz(r, theta, phi):
    """
    Calculate xyz coordinates from the spherical data
    Right-hand coordinate system
    """
    x = r * np.sin(theta) * np.sin(phi)
    y = r * np.sin(theta) * np.cos(phi)
    z = r * np.cos(theta)

    return x,y,z


def xyz2rza(x, y, z):
    """
    Calculate spherical coordinates from the xyz data
    """
    r = np.sqrt(x**2 + y**2 + z**2)
    theta = np.arccos(z / r)
    phi = np.arctan2(x, y)
    if np.isscalar(phi):
        phi = phi+2*np.pi if x < 0 else phi
        phi = phi-2*np.pi if x > (2*np.pi) else phi
    else:
        np.add(phi, 2*np.pi, out=phi, where=x < 0)
        np.subtract(phi, 2*np.pi, out=phi, where=x > (2*np.pi))

    return r, theta, phi

