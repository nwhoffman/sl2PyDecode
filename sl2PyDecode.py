
# coding: utf-8

# In[1]:

## This script reads in a binary .sl2 (sonar) file, converts the coordinates
## to latitude, longitude, and the depth at those locations.
## A .csv file is the output and includes lat, long, and depth columns.
## A simple plot is also created to visualize the depth profile.

# Imports
import os
import math
import numpy as np
import csv

# Imports for matplotlib (backend)
import matplotlib
matplotlib.use('Agg') #avoids some import errors
from matplotlib import pyplot as plt

# Constants for conversions
rad_polar = 6356752.3142 # polar radius of the Earth
max_uint4 = 4294967295 # max value for a 4 byte unsigned integer
feet2m = 1/3.2808399  # feet to meter conversions


# In[2]:

# Interactive - user enters the filename in the terminal
sl2file = input('Please enter the name of your .sl2 file (with .sl2 extension): ')


# In[3]:

# Open .sl2 file and read the data into a list

with open(sl2file, "rb") as myfile:
    
    # find the size of the file (in bytes)
    sl2file_size = os.path.getsize(sl2file)
    print('File size (bytes) :', sl2file_size)
    print('Decoding....(may take a few seconds)')
    
    # block sizes dtype
    dt_block = np.dtype({'blockSize': ('<u2', 26)})
    
    block_offset = 10 # file header is 10 bytes
    block_offset_list = [] # empty list for block locations
    
    while block_offset < sl2file_size:
        myfile.seek(block_offset,0) # start at the beginning of each block
        
        block_size = np.fromfile(myfile, dtype=dt_block, count=1) # read the block size
        block_offset = block_offset + block_size[0][0] # increase the block position marker
        block_offset_list.append(block_offset) # list of offsets to use later

    # Using the block size, read the rest of the data from each block
    sl2blocks_dtype = np.dtype(dict(
      names=['depth', 'longitude', 'latitude'],
      offsets=[62, 106, 110], # counted from start of the block in bytes (??)
      formats=["f4", "<u4", "<u4"],
    ))

    i=0 # position in block_offset_list
    block_data = [] # list to hold the data
    
    old_lat = 0 # compare latitudes for duplicates
    for i in range(len(block_offset_list)-1): #last block, no data??
        
        myfile.seek(block_offset_list[i],0) # find the beginning of each block
        data_array = np.fromfile(myfile, dtype=sl2blocks_dtype, count=1) #get data
        
        # get data from the array
        depth = data_array[0][0]
        lon = data_array[0][1]
        lat = data_array[0][2]
             
        # filter out depth=0 and duplicates in latitude/longitude
        if depth != 0 & lat != old_lat:  # not quite working for duplicates?       
        
            # convert depth to meters (negative depth)
            depthM = (depth * feet2m)*-1
            # convert coords to degrees
            longitude = (lon - max_uint4) / rad_polar * (180/math.pi)
            latitude = ((2*math.atan(math.exp(lat/rad_polar)))-(math.pi/2)) * (180/math.pi)
        
            # fill a list with dictionaries
            block = {'waterDepthM': depthM, 'longitude': longitude, 'latitude': latitude }
            block_data.append(block)
        
        # compare with latitude on the next loop (removes duplicates?)
        old_lat = lat
       

myfile.close() # close the file opened in the while loop
print('Decoding complete. Number of blocks decoded: ', len(block_data))


# In[4]:

# Convert the list of dict to .csv file
output = sl2file + '_output.csv'
print('The output .csv file is: ', output)

keys = block_data[0].keys()
with open(output, 'w', newline='') as output_file:
    fieldnames = ['latitude', 'longitude', 'waterDepthM']
    dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    dict_writer.writeheader()
    dict_writer.writerows(block_data)
    
output_file.close()  


# In[5]:

# Make separate lists for depth and coordinates (for plotting)
d_plt = [d['waterDepthM'] for d in block_data]
lon_plt = [d['longitude'] for d in block_data]
lat_plt = [d['latitude'] for d in block_data]


# In[6]:

## scatter plot with circle colour representing depth
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(111)

cax = plt.scatter(lon_plt, lat_plt, c=d_plt, 
                  s=10, cmap='viridis', alpha=0.6)

# Plot the colorbar
cbar = fig.colorbar(cax)
cbar.set_label('Depth (m)', labelpad=10)

# Set the axes limits, labels, title
plt.title(sl2file)
plt.xticks(rotation=90)
ax.set_xlim(min(lon_plt), max(lon_plt))
ax.set_ylim(min(lat_plt), max(lat_plt))
ax.ticklabel_format(useOffset=False)
ax.set_aspect('equal')

# save the plot as a .png instead of showing
plot_name = sl2file + '_image.png'
print('The output image is: ', plot_name)
fig.savefig(plot_name, dpi=100)

