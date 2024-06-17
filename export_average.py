import netCDF4 as nc
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os
from cut_map import cut_rasters


def export_raster(dataset, file_name, specific_variable):

    # Get the current script directory
    current_path = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_path, 'outputs')
    output_path_folder = os.path.join(output_path, file_name)
    shp_path = os.path.join(current_path, 'shp', "limite_nacional_2011", "limite_nacional_2011.shp")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if not os.path.exists(output_path_folder):
        os.makedirs(output_path_folder)


    # Check if the specific variable is in the file
    if specific_variable not in dataset.variables:
        raise ValueError(f"The variable '{specific_variable}' is not found in the NetCDF file.")

    var_output = os.path.join(output_path_folder, specific_variable)

    if not os.path.exists(var_output):
        os.makedirs(var_output)

    # Extract variables
    var_data = dataset.variables[specific_variable][:]

    # Check dimensions
    print(f"Dimensions of {specific_variable}: {var_data.shape}")

    # Assume dimensions are [time, lat, lon]
    time_index = 0  # Select a time index for coordinates

    lat = dataset.variables['XLAT'][time_index, :, 0]  # Assuming XLAT is 3D [time, lat, lon]
    lon = dataset.variables['XLONG'][time_index, 0, :]  # Assuming XLONG is 3D [time, lat, lon]

    inv_lat = np.flip(lat, axis=0)

    res_lat = abs(inv_lat[1] - inv_lat[0])
    res_lon = abs(lon[1] - lon[0])
    transform = from_origin(lon.min(), inv_lat.max(), res_lon, res_lat)

    # Calculate the accumulated sum of bands for the specific variable
    result_variable = np.sum(var_data, axis=0) if specific_variable == "RAINNC" else np.mean(var_data, axis=0)

    # Create a unique name for the raster file
    raster_filename = os.path.join(var_output, f'{specific_variable}_raster.tif')

    # Create the raster file with the accumulated sum or the mean as a single band
    with rasterio.open(
            raster_filename,
            'w',
            driver='GTiff',
            height=result_variable.shape[0],
            width=result_variable.shape[1],
            count=1,  # Only one band for the accumulated sum or the mean
            dtype=result_variable.dtype,
            crs='+proj=latlong',
            transform=transform,
    ) as dst:
        dst.write(result_variable, 1)

    print(f"Raster created successfully")

    cut_rasters(raster_filename, shp_path)

    print(f"Raster cut successfully as '{raster_filename}'")

    return result_variable

