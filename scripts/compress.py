import os
import geopandas as gpd
from shapely.geometry import Point
import math

# Set the center coordinates and radius in decimal degrees
center_latitude = -36.8509
center_longitude = 174.7645
radius_km = 30.0

# Get the path to the user's home directory
home_dir = os.path.expanduser("~")

# Construct the path to the Downloads folder
downloads_folder = os.path.join(home_dir, 'Downloads')

# Construct the path to the input GeoJSON file in the Downloads folder
input_geojson_file = os.path.join(downloads_folder, 'Water_Pipe.geojson')
gdf = gpd.read_file(input_geojson_file)

# Create a point geometry for the center coordinates
center_point = Point(center_longitude, center_latitude)

# Convert the radius from kilometers to degrees
radius_deg = radius_km / 111.32

# Filter the data within the specified radius
filtered_gdf = gdf[gdf.geometry.distance(center_point) <= radius_deg]

# Save the filtered data to a new GeoJSON file
output_geojson_file = os.path.join(downloads_folder, 'water-pipe-compressed.geojson')
filtered_gdf.to_file(output_geojson_file, driver='GeoJSON')