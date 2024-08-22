import netCDF4 as nc
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os
from .cut_map import cut_rasters
from .generate_images import generate_image
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def export_raster(dataset, file_name, specific_variable, output_path, inputs_path, is4Dim=False):
    # Get the current script directory
    output_path_folder = os.path.join(output_path, file_name)
    shape_path = os.path.join(inputs_path, "shapefile")
    data_path = os.path.join(inputs_path, "data")
    shp_path = os.path.join(shape_path, "limite_nacional", "limite_nacional.shp")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if not os.path.exists(output_path_folder):
        os.makedirs(output_path_folder)

    var_output = os.path.join(output_path_folder, specific_variable)

    if not os.path.exists(var_output):
        os.makedirs(var_output)

    # Extract variables
    if specific_variable == "RAIN":
        if "RAINNC" not in dataset.variables or "RAINC" not in dataset.variables or "RAINSH" not in dataset.variables:
            raise ValueError(f"The variables 'RAINNC', 'RAINC' or 'RAINSH' are not found in the NetCDF file.")
        rainnc_data = dataset.variables["RAINNC"][:]
        rainc_data = dataset.variables["RAINC"][:]
        rainsh_data = dataset.variables["RAINSH"][:]
        var_data = rainnc_data + rainc_data + rainsh_data
    else:
        if specific_variable not in dataset.variables:
            raise ValueError(f"The variable '{specific_variable}' is not found in the NetCDF file.")
        var_data = dataset.variables[specific_variable][:]
    
    # Check dimensions
    print(f"Dimensions of {specific_variable}: {var_data.shape}")

    if is4Dim:
        var_data = var_data[:, 0, :, :]

    # Assume dimensions are [time, lat, lon]
    time_index = 0  # Select a time index for coordinates

    lat = dataset.variables['XLAT'][time_index, :, 0]  # Assuming XLAT is 3D [time, lat, lon]
    lon = dataset.variables['XLONG'][time_index, 0, :]  # Assuming XLONG is 3D [time, lat, lon]

    inv_lat = np.flip(lat, axis=0)

    res_lat = abs(inv_lat[1] - inv_lat[0])
    res_lon = abs(lon[1] - lon[0])
    transform = from_origin(lon.min(), inv_lat.max(), res_lon, res_lat)

    if specific_variable == "T2":
        var_data = var_data - 273

    xtime = dataset.variables['XTIME'][:]

    previous_day = np.zeros(var_data.shape[1:])
    # Iterate over each day (8 intervals per day)
    for day in range(var_data.shape[0] // 8):
        start_index = day * 8
        end_index = start_index + 8

        start_date_str = dataset.START_DATE
        start_datetime = datetime.strptime(start_date_str, '%Y-%m-%d_%H:%M:%S')

        date = start_datetime + timedelta(minutes=int(xtime[start_index]))
        date = date.strftime('%Y-%m-%d')

        daily_data = var_data[start_index:end_index, :, :]

        # Calculate the accumulated sum or mean of the daily data
        if specific_variable == "RAIN":
            # Initialize the previous total for 3-hour difference calculation
            previous_total = np.zeros(daily_data.shape[1:])
            result_variable = np.zeros(daily_data.shape[1:])
            for i in range(daily_data.shape[0]):
                current_total = daily_data[i, :, :] - previous_day
                # Calculate the 3-hourly accumulated precipitation
                result_variable += current_total - previous_total
                previous_total = current_total
            if day == 0 or day == 1:
                result_variable = result_variable * 0.6
        else:
            result_variable = np.mean(daily_data, axis=0)
        previous_day += result_variable
        # Create a unique name for the raster file
        raster_filename = os.path.join(var_output, f'{specific_variable}_{date}_raster.tif')

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

        print(f"Raster for: {specific_variable} day: {date} created successfully")

        new_raster_filename = cut_rasters(raster_filename, shp_path)

        print(f"Raster for: {specific_variable} day: {date} cut successfully as '{new_raster_filename}'")

        generate_image(new_raster_filename, search_csv(os.path.join(data_path, "ranges"), specific_variable), data_path, os.path.join(shape_path, "limites_municipales", "limite_municipal.shp"))

    return var_output


def search_csv(ranges_path, varname):
    csvs = [os.path.join(ranges_path, file) for file in os.listdir(ranges_path)]

    def contains_keyword(file_name, keyword):
        return file_name.startswith(keyword)

    filtered_files = [file for file in csvs if contains_keyword(os.path.basename(file), varname)]

    if not filtered_files:
        filtered_files.append(os.path.join(ranges_path, "ranges_Default.csv"))

    return filtered_files[0]
