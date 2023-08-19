import os
import geopandas as gpd
from shapely.geometry import Point
import math
import re
from geopy.distance import geodesic

# Set the center coordinates and radius in decimal degrees
# -36.865164138579374, 174.75606736112917
centre_coords = (-36.8651, 174.7560)
radius_km = 15.0

# Get the path to the user's home directory
home_dir = os.path.expanduser("~")

# Construct the path to the Downloads folder
downloads_folder = os.path.join(home_dir, 'Downloads')

# Construct the path to the input GeoJSON file in the Downloads folder
input_geojson_file = os.path.join(downloads_folder, 'suburbs.geojson')
gdf = gpd.read_file(input_geojson_file)


# Create a function to calculate distance between two points
def calculate_distance(row):
    suburb_coords = (row['geometry'].centroid.y, row['geometry'].centroid.x)
    return geodesic(suburb_coords, centre_coords).kilometers


# Filter the suburbs within Xkm of the centre
filtered_suburbs = []

# Calculate the distance between each suburb and the centre
gdf['distance_to_centre'] = gdf.apply(calculate_distance, axis=1)

# Filter the suburbs within Xkm of the centre
filtered_gdf = gdf[gdf['distance_to_centre'] <= radius_km]

suburb_names = list(filtered_gdf['name'])
cleaned_names = []
for name in suburb_names:
    cleaned = re.sub(r'[\/:*?"<>|]+', '_', name.strip())
    cleaned = cleaned.replace(' ', '_')
    cleaned_names.append(cleaned)

cleaned_names.sort()
# Save the filtered data to a new GeoJSON file
output_geojson_file = os.path.join(downloads_folder, 'suburb-list.geojson')
output_txt_file = os.path.join(downloads_folder, 'suburb-list.txt')
with open(output_txt_file, 'w') as file:
    for item in cleaned_names:
        file.write(item + '\n')

filtered_gdf.to_file(output_geojson_file, driver='GeoJSON')
