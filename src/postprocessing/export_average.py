import netCDF4 as nc
import numpy as np
import rasterio
import xarray as xr
import rioxarray
import geopandas as gpd
from shapely.geometry import mapping
from rasterio.transform import from_origin
import os
from .cut_map import cut_rasters
from .generate_images import generate_image
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pandas as pd
import matplotlib

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
        if "RAINNC" not in dataset.data_vars or "RAINC" not in dataset.data_vars or "RAINSH" not in dataset.data_vars:
            raise ValueError(f"The variables 'RAINNC', 'RAINC' or 'RAINSH' are not found in the NetCDF file.")
        rainnc_data = dataset.RAINNC
        rainc_data = dataset.RAINC
        rainsh_data = dataset.RAINSH
        var_data = rainnc_data + rainc_data + rainsh_data
    else:
        if specific_variable not in dataset.data_vars:
            raise ValueError(f"The variable '{specific_variable}' is not found in the NetCDF file.")
        var_data = dataset[specific_variable][:]
    
    var_data.rio.write_crs("EPSG:4326")

    # Check dimensions
    print(f"Dimensions of {specific_variable}: {var_data.shape}")

    if is4Dim:
        if  "bottom_top" in var_data.dims:
            var_data = var_data.isel(bottom_top=0)
        elif "soil_layers_stag" in var_data.dims:
            var_data = var_data.isel(soil_layers_stag=0)


    lat = pd.to_numeric(dataset.XLAT.isel(Time=0, west_east=0).values)
    long = pd.to_numeric(dataset.XLONG.isel(Time=0, south_north=0).values)

    #inv_lat = np.flip(lat, axis=0)


    if specific_variable == "T2":
        var_data.values = var_data.values - 273

    xtime = dataset.XTIME

    previous_day = np.zeros(var_data.shape[1:])

    if "d01" in file_name:
        shp_path = os.path.join(shape_path, "limite_caribe", "limite_caribe.shp")

    shapefile = gpd.read_file(shp_path)

    shapefile = shapefile.to_crs("EPSG:4326")

    # Iterate over each day (8 intervals per day)
    for day in range(var_data.shape[0] // 8):
        start_index = day * 8
        end_index = start_index + 8

        start_date_str = dataset.START_DATE
        start_datetime = datetime.strptime(start_date_str, '%Y-%m-%d_%H:%M:%S')

        date = start_datetime + timedelta(minutes=int(xtime[start_index]))
        date = date.strftime('%Y-%m-%d')

        daily_data = var_data.isel(Time=slice(start_index, end_index))

        data = daily_data

        # Calculate the accumulated sum or mean of the daily data
        if specific_variable == "RAIN":
            # Initialize the previous total for 3-hour difference calculation
            previous_total = np.zeros(daily_data.shape[1:])
            result_variable = np.zeros(daily_data.shape[1:])
            for i in range(daily_data.shape[0]):
                current_total = daily_data.isel(Time=i) - previous_day
                # Calculate the 3-hourly accumulated precipitation
                result_variable += current_total - previous_total
                previous_total = current_total
            if day == 0 or day == 1:
                result_variable = result_variable * 0.6
            
            result_variable_expanded = np.expand_dims(result_variable, axis=0)  # (1, y, x)

            # Replicate across the Time dimension to match data's shape (Time, y, x)
            result_variable_expanded = np.repeat(result_variable_expanded, daily_data.shape[0], axis=0)

            # Assign to data with matching dimensions
            data.values = result_variable_expanded
            previous_day += result_variable

        else:
            
            mean = np.mean(daily_data.values, axis=0)
            mean_expanded = np.expand_dims(mean, axis=0)
            mean_expanded = np.repeat(mean_expanded, daily_data.shape[0], axis=0)
            data.values = mean_expanded
            
        # Create a unique name for the raster file
        raster_filename = os.path.join(var_output, f'{specific_variable}_{date}.tif')
        time = list(range(start_index, end_index))
        data_xarray =xr.DataArray(data.values, dims=['t','y','x'], coords={'t': time,'y': lat,'x': long})
        
        data_result = data_xarray.rio.write_crs("EPSG:4326").rio.clip(shapefile.geometry, shapefile.crs)
        
        data_result = data_result.isel(t=0)

        save_raster(data_result, raster_filename)

        print(f"Raster for: {specific_variable} day: {date} created successfully")


        shape_cut_path = os.path.join(shape_path, "limites_municipales", "limite_municipal.shp")

        if "d01" in file_name:
            shape_cut_path = os.path.join(shape_path, "limite_caribe", "limite_caribe.shp")

        generate_image(raster_filename, search_csv(os.path.join(data_path, "ranges"), specific_variable), data_path, shape_cut_path)

    return var_output


def search_csv(ranges_path, varname):
    csvs = [os.path.join(ranges_path, file) for file in os.listdir(ranges_path)]

    def contains_keyword(file_name, keyword):
        return file_name.startswith(keyword)

    filtered_files = [file for file in csvs if contains_keyword(os.path.basename(file), varname)]

    if not filtered_files:
        filtered_files.append(os.path.join(ranges_path, "ranges_Default.csv"))

    return filtered_files[0]


def save_raster(data_array, output_path):
    if isinstance(data_array, xr.Dataset):
        # Asumiendo que necesitas un DataArray específico dentro del Dataset
        data_array = data_array.to_array().isel(variable=0)  # Modifica según sea necesario para obtener el DataArray correcto

    lon = data_array.coords['x']
    lat = data_array.coords['y']

    # Voltear el array de datos a lo largo del eje de latitud
    flipped_data = np.flip(data_array.values, axis=0)
    
    transform = from_origin(west=lon.min().item(), north=lat.max().item(), xsize=(lon.max().item()-lon.min().item())/len(lon), ysize=(lat.max().item()-lat.min().item())/len(lat))

    # Guardar como un archivo raster
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=flipped_data.shape[0],
        width=flipped_data.shape[1],
        count=1,
        dtype=flipped_data.dtype,
        crs='+proj=latlong',
        transform=transform,
    ) as dst:
        dst.write(flipped_data, 1)
