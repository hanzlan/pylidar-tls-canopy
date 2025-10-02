import riegl_rdb
import riegl_rxp
import ast
import matplotlib.pyplot as plt
import numpy as np
import math
from collections import Counter
import pandas as pd


file_converted_on_import = riegl_rdb.readFile("/Stor2/karun/data/filtering_tests/rdb/240408_121822_converted_on_import.rdbx")
file_existing_in_project = riegl_rdb.readFile("/Stor2/karun/data/filtering_tests/rdb/240408_121822_exisiting_in_proj.rdbx")
file_explicitly_converted = riegl_rdb.readFile("/Stor2/karun/data/filtering_tests/rdb/240408_121822_explicitly_converted.rdbx")
file_rxp = riegl_rxp.readFile("/Stor2/karun/data/filtering_tests/rdb/240408_121822.rxp")


pulse_cols = ['zenith','azimuth','target_count']
point_cols = ['x','y','z','range','target_index',
              'zenith','azimuth','target_count']

pulses = {}

with riegl_io.RXPFile("/Stor2/karun/data/filtering_tests/rdb/240408_121822.rxp") as rxp:
            for col in pulse_cols:
                pulses[col] = rxp.get_data(col, return_as_point_attribute=False)


file_rxp[1].shape
file_converted_on_import[1].shape
file_explicitly_converted[1].shape
file_existing_in_project[1].shape


file_rxp[1][0:50]
file_converted_on_import[1][0:50]

file_rxp[1].dtype.names
file_converted_on_import[1].dtype.names

unique_vals, counts = np.unique(file_rxp[1]['pulse_id'], return_counts=True)
frequency_dict = dict(zip(unique_vals, counts))
print(frequency_dict)

np.unique(counts, return_counts=True)


np.sort(file_converted_on_import[1]['timestamp'])
(np.sort(np.round(file_rxp[1]['timestamp'],  decimals = 6)))
(np.sort(np.round(file_converted_on_import[1]['timestamp'],  decimals = 6)))

len(file_rxp[1])-len(file_converted_on_import[1])
mask = np.isin(np.sort(np.round(file_rxp[1]['timestamp'],  decimals = 6)), np.sort(np.round(file_converted_on_import[1]['timestamp'],  decimals = 6)))
file_rxp2 = np.sort(np.round(file_rxp[1]['timestamp'],  decimals = 6))[~mask]
len(file_rxp2)

len()

# Extract the "range" field from each array
range_values1 = np.sort((file_converted_on_import[1]['reflectance']))
range_values2 = np.sort((file_explicitly_converted[1]['reflectance']))
range_values3 = np.sort((file_existing_in_project[1]['reflectance']))
range_values4 = np.sort((file_rxp[1]['reflectance']))



# Create a new figure with 1 row and 3 columns of subplots that share the same x and y axes
fig, axs = plt.subplots(1, 4, figsize=(18, 5), sharex=True, sharey=True)

# Plot histogram for File 1
axs[0].hist(range_values1, bins = 30, edgecolor='black', color='skyblue')
axs[0].set_title('File 1')
axs[0].set_xlabel('Range Values')
axs[0].set_ylabel('Frequency')

# Plot histogram for File 2
axs[1].hist(range_values2, bins = 30, edgecolor='black', color='salmon')
axs[1].set_title('File 2')
axs[1].set_xlabel('Range Values')

# Plot histogram for File 3
axs[2].hist(range_values3, bins = 30, edgecolor='black', color='limegreen')
axs[2].set_title('File 3')
axs[2].set_xlabel('Range Values')

# Plot histogram for File 4
axs[3].hist(range_values4, bins = 30, edgecolor='black', color='limegreen')
axs[3].set_title('File 4')
axs[3].set_xlabel('Range Values')

# Set a common title for the figure
plt.suptitle('Histogram of Range Values for Three Files', fontsize=16)



# Adjust layout so labels and titles don't overlap
plt.tight_layout(rect=[0, 0, 1, 0.95])

# Save the figure (optional)
plt.savefig("/home/kdayal/projects/pylidar-tls-canopy/results/three_files_histogram_panels.png", dpi=300, bbox_inches="tight")


