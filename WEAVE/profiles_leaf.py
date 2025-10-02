import os
import glob
from datetime import datetime
import pandas as pd
import concurrent.futures
import time
import os
import glob
import time
import datetime
import numpy as np
from scipy.optimize import curve_fit,minimize
import matplotlib.pyplot as plt


from pylidar_tls_canopy import leaf_io, plant_profile, grid, visualize
from pylidar_tls_canopy.rsmooth import rsmooth



def parse_filename(filename):
    """
    Parse a filename of the form:
      sensor_scanNumber_scanType_date-time_zenithShots_azimuthShots.csv
    For example:
      ESS00335_0001_hemi_20241009-134747Z_0800_0400.csv

    Returns a dictionary with the parsed components.
    """
    filename = "/Stor2/karun/data/benchmarking/leaf/berchtesgaden/004/data/ESS00337_0001_hinge_20241014-152801Z_0001_8500.csv"
    base = os.path.basename(filename)


    if base.lower().endswith(".csv"):
        base = base[:-4]  # Remove the .csv extension

    parts = base.split('_')
    if len(parts) != 6:
        raise ValueError(f"Unexpected format in filename '{filename}'. Expected 6 underscore-separated parts, got {len(parts)}.")

    sensor = parts[0]
    scan_number = parts[1]
    scan_type = parts[2]

    # The date and time are combined in the fourth part, separated by a hyphen.
    date_time_part = parts[3]
    if '-' not in date_time_part:
        raise ValueError(f"Date and time part missing '-' in filename '{filename}'.")
    date_str, time_str = date_time_part.split('-', 1)
    
    # Remove a trailing "Z" if present, then combine date and time strings.
    time_str = time_str.rstrip("Z")
    # For example, if date_str is "20241009" and time_str is "134747",
    # we create a datetime object. Adjust the format string as needed.
    dt_str = f"{date_str} {time_str}"
    dt_format = "%Y%m%d %H%M%S"
    try:
        dt_object = datetime.strptime(dt_str, dt_format)
    except Exception as e:
        raise ValueError(f"Error parsing date/time in '{filename}': {e}")

    zenith_shots = parts[4]
    azimuth_shots = parts[5]
    
    # Get file size in bytes
    file_size_bytes = os.path.getsize(filename)
    
    # Convert to KB, MB, etc.
    file_size_kb = file_size_bytes / 1024
    file_size_mb = file_size_kb / 1024

    return {
        "full_path": os.path.abspath(filename),
        "sensor": sensor,
        "scan_number": scan_number,
        "scan_type": scan_type,
        "datetime": dt_object,  # datetime object combining date and time
        "zenith_shots": zenith_shots,
        "azimuth_shots": azimuth_shots,
        "file_size_mb": file_size_mb
    }

def create_dataframe(root_dir):
    """
    Searches recursively for CSV files in the root_dir, parses their filenames,
    and returns a Pandas DataFrame containing the extracted information.
    """
    # Recursively find all CSV files in the given directory
    file_pattern = os.path.join("/Stor2/karun/data/benchmarking/leaf/berchtesgaden/004/data/", "**", "*.csv")
    files = glob.glob(file_pattern, recursive=True)
    
    records = []
    for file in files:
        try:
            record = parse_filename(files[0])
            records.append(record)
        except Exception as e:
            print(f"Skipping file {file} due to error: {e}")

    # Create DataFrame from the list of dictionaries
    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    # Set the directory to search (adjust as needed)
    directory_to_search = "/Stor2/karun/data/benchmarking/leaf/berchtesgaden/004/data/"  # current directory or specify your path
    df = create_dataframe(directory_to_search)
    print(df)

df = df.sort_values(by="datetime")

#filter out on the benchmarking scans
# Example target date as a string
targetdate = "2024-10-16"

# Convert targetdate to a date object
target_date_obj = pd.to_datetime(targetdate).date()

# Convert the time condition string to a datetime object
time_limit = pd.to_datetime("2024-10-16 15:30:30")

# Now filter the DataFrame

df = df[
    (df['datetime'] < time_limit) &
    (df['datetime'].dt.date == target_date_obj)]

df = df.reset_index(drop=True)


def process_file(full_path, sensor, scan_type, zenith_shots, azimuth_shots):
    
    # Example of reading a file (modify as per your file type)
    sensor_height = 1.7 # Height above ground of the sensor head (m)
    max_h = 40 # Maximum height for visualization (m)
    max_pai = None # Maximum PAI for visualization
    hres = 0.5 # Vertical resolution of profiles (m)
    zenith_offset = 0 # Fixed zenith offset for LEAF scans (rad)
    
    try:
        vpp = plant_profile.Jupp2009(hres=hres, zres=5, ares=90, min_z=5, max_z=70, min_h=0, max_h=max_h)
        valid = vpp.add_leaf_scan_position(full_path, method='FIRSTLAST', zenith_offset=zenith_offset, 
                                   min_zenith=5, max_zenith=70, sensor_height=sensor_height)
        if valid:
            vpp.get_pgap_theta_z()
            
            hinge_pai = vpp.calcHingePlantProfiles()
            hinge_pavd = vpp.get_pavd(hinge_pai)

            weighted_pai = vpp.calcSolidAnglePlantProfiles()
            weighted_pavd = vpp.get_pavd(weighted_pai)

            linear_pai = vpp.calcLinearPlantProfiles()
            linear_pavd = vpp.get_pavd(linear_pai)
            
        
        prof_dict = {"hinge_pai":hinge_pai, 
                    "weighted_pai":weighted_pai, 
                    "linear_pai":linear_pai, 
                    "hinge_pavd":hinge_pavd, 
                    "linear_pavd":weighted_pavd, 
                    "weighted_pavd":linear_pavd}
        
        print(f"Processed {full_path}")
        return prof_dict
    
    except FileNotFoundError:
        print(f"File not found: {full_path}")
        return None
    
results = df.apply(
    lambda row: process_file(row['full_path'], row['sensor'], row['scan_type'], row['zenith_shots'], row['azimuth_shots']),
    axis=1
)



# Example of reading a file (modify as per your file type)
sensor_height = 1.7 # Height above ground of the sensor head (m)
max_h = 40 # Maximum height for visualization (m)
max_pai = None # Maximum PAI for visualization
hres = 0.5 # Vertical resolution of profiles (m)
zenith_offset = 0 # Fixed zenith offset for LEAF scans (rad)
vpp = plant_profile.Jupp2009(hres=hres, zres=5, ares=90, min_z=5, max_z=70, min_h=0, max_h=max_h)
valid = vpp.add_leaf_scan_position(df['full_path'][3], method='FIRSTLAST', zenith_offset=zenith_offset, 
                                   min_zenith=5, max_zenith=70, sensor_height=sensor_height)
vpp.get_pgap_theta_z()
            
hinge_pai = vpp.calcHingePlantProfiles()
hinge_pavd = vpp.get_pavd(hinge_pai)

weighted_pai = vpp.calcSolidAnglePlantProfiles()
weighted_pavd = vpp.get_pavd(weighted_pai)

linear_pai = vpp.calcLinearPlantProfiles()
linear_pavd = vpp.get_pavd(linear_pai)


%matplotlib inline
# Create the plot
plt.figure(figsize=(8, 5))

plt.plot(hinge_pavd)
plt.plot(weighted_pavd)
plt.plot(linear_pavd)

