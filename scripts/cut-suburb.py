import geopandas as gpd
from shapely.geometry import LineString

# Load the large GeoJSON file with pipe data
pipes_gdf = gpd.read_file('large_pipes.geojson')

# Load the GeoJSON file with suburb boundaries
suburbs_gdf = gpd.read_file('suburbs.geojson')

# Create a dictionary to store GeoDataFrames for each suburb
suburb_dataframes = {}

# Iterate through each suburb
for index, suburb in suburbs_gdf.iterrows():
    # Extract the suburb name and remove whitespace
    suburb_name = suburb['suburb_name'].replace(' ', '_')

    # Initialize an empty GeoDataFrame for the current suburb
    suburb_gdf = gpd.GeoDataFrame(columns=pipes_gdf.columns)

    # Iterate through each pipe feature
    for _, pipe in pipes_gdf.iterrows():
        # Clip the pipe line with the suburb boundary
        clipped_pipe = pipe.geometry.intersection(suburb.geometry)

        # Check if the intersection resulted in a LineString or MultiLineString
        if clipped_pipe.type == 'LineString':
            suburb_gdf = suburb_gdf.append(pipe, ignore_index=True)
        elif clipped_pipe.type == 'MultiLineString':
            for line_segment in clipped_pipe:
                suburb_gdf = suburb_gdf.append({'geometry': line_segment}, ignore_index=True)

    # Add the suburb's data to the dictionary
    suburb_dataframes[suburb_name] = suburb_gdf

# Save each suburb's data to separate GeoJSON files
for suburb_name, suburb_gdf in suburb_dataframes.items():
    output_filename = f'{suburb_name}_pipes.geojson'
    suburb_gdf.to_file(output_filename, driver='GeoJSON')

print("Done! Separate GeoJSON files for each suburb have been created.")
