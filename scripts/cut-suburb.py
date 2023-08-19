import geopandas as gpd
from shapely.geometry import LineString
import os
import pandas as pd
from multiprocessing import Manager, Pool, cpu_count
from flock import LOCK_EX
import re
import fcntl

# Determine the number of CPU cores available
num_cores = cpu_count()

# Define the maximum number of worker processes or threads (adjust as needed)
max_workers = min(num_cores, 6)  # Limit to a reasonable number, like 4

# Get the path to the user's home directory
home_dir = os.path.expanduser("~")

# Construct the path to the Downloads folder
downloads_folder = os.path.join(home_dir, 'Downloads')

# Construct the path to the input GeoJSON file in the Downloads folder
pipes_file = os.path.join(downloads_folder, 'Water_Pipe_top15.geojson')
suburbs_file = os.path.join(downloads_folder, 'suburb-list.geojson')
matched_names = os.path.join(downloads_folder, 'suburb-list.txt')

# Load the list of suburb names from a text file into a set
matched_names_set = set()

with open(matched_names, 'r') as file:
    for line in file:
        matched_names_set.add(line.strip())

print("Loading suburbs")
# Load the GeoJSON file with suburb boundaries
suburbs_gdf = gpd.read_file(suburbs_file)

print("Loading pipes file")
# Load the large GeoJSON file with pipe data
pipes_gdf = gpd.read_file(pipes_file)

# Maintain a set of processed suburb geometries
processed_suburbs = set()

# Create a spatial index for suburbs_gdf for efficient spatial join
suburbs_gdf.sindex


# Function to clean suburb names
def clean_suburb_name(suburb_name):
    # Replace invalid characters and spaces with underscores
    cleaned = re.sub(r'[\/:*?"<>|]+', '_', suburb_name.strip())
    cleaned = cleaned.replace(' ', '_')
    return cleaned


def process_suburb(suburb_geometry):
    if suburb_geometry in processed_suburbs:
        return

    # Use spatial join to find the matching suburb
    possible_matches_index = list(suburbs_gdf.sindex.intersection(suburb_geometry.bounds))
    possible_matches = suburbs_gdf.iloc[possible_matches_index]
    exact_match = possible_matches[possible_matches.intersects(suburb_geometry)]

    if not exact_match.empty:
        suburb_name = exact_match['name'].values[0]
        # Clean the suburb name
        cleaned_suburb_name = clean_suburb_name(suburb_name)
        if cleaned_suburb_name not in matched_names_set:
            return

        print(f'Clipping suburb: {cleaned_suburb_name}')

        # Initialize an empty GeoDataFrame for the current suburb
        suburb_gdf = gpd.GeoDataFrame(columns=pipes_gdf.columns)

        # Iterate through each pipe feature
        for _, pipe in pipes_gdf.iterrows():
            # Clip the pipe line with the suburb boundary
            clipped_pipe = pipe.geometry.intersection(suburb_geometry)

            # Check if the intersection resulted in a LineString or MultiLineString
            if clipped_pipe.geom_type == 'LineString':
                # Convert the clipped_pipe to a GeoSeries and then to a GeoDataFrame
                clipped_pipe = gpd.GeoSeries(clipped_pipe)
                clipped_pipe = gpd.GeoDataFrame({'geometry': clipped_pipe})

                suburb_gdf = pd.concat([suburb_gdf, clipped_pipe], ignore_index=True)
            elif clipped_pipe.geom_type == 'MultiLineString':
                for line_segment in clipped_pipe:
                    # Convert the line_segment to a GeoSeries and then to a GeoDataFrame
                    line_segment = gpd.GeoSeries(line_segment)
                    line_segment = gpd.GeoDataFrame({'geometry': line_segment})

                    suburb_gdf = pd.concat([suburb_gdf, line_segment], ignore_index=True)

        print(f"Saving suburb file for {cleaned_suburb_name}")
        # Save the suburb's data to a separate GeoJSON file
        output_filename = f'suburbs/{cleaned_suburb_name}_pipes.geojson'
        # Acquire a lock on the file
        file_lock = open(output_filename, 'w')
        fcntl.lockf(file_lock, fcntl.LOCK_EX)
        # Use file locking to prevent write conflicts
        try:
            # Check if the file exists and delete it if it does
            if os.path.exists(output_filename):
                os.remove(output_filename)

            # Save the suburb's data to a separate GeoJSON file
            suburb_gdf.to_file(output_filename, driver='GeoJSON')
            # Mark this suburb as processed to avoid duplicate processing
            processed_suburbs.add(suburb_geometry)
        finally:
            file_lock.close()


# Use multiprocessing to process suburbs in parallel
if __name__ == '__main__':
    with Pool(max_workers) as pool:
        pool.map(process_suburb, suburbs_gdf.geometry)
print("Done! Separate GeoJSON files for each suburb have been created.")
