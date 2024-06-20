import os
import netCDF4 as nc
import numpy as np
import rasterio as rio
from rasterio.transform import from_origin
from .export_average import export_raster
from .generate_images import generate_image
import rasterio


def extract_data(inputs_path, outputs_path):

    
    wrf_inputs_path = os.path.join(inputs_path, "wrf")

    # Filtrar solo los archivos
    nc_files = [os.path.join(wrf_inputs_path, file) for file in os.listdir(wrf_inputs_path)]

    for file in nc_files:

        file_name = os.path.basename(file)
        print(f"Procesando el archivo: {file_name}")

        dataset = nc.Dataset(file)

        T2 = export_raster(dataset, file_name, "T2", outputs_path, inputs_path)

        RAINNC = export_raster(dataset, file_name, "RAINNC", outputs_path, inputs_path)
        
        HGT = export_raster(dataset, file_name, "HGT", outputs_path, inputs_path)
        
        SWDOWN = export_raster(dataset, file_name, "SWDOWN", outputs_path, inputs_path)

        U10 = export_raster(dataset, file_name, "U10", outputs_path, inputs_path)
        
        V10 = export_raster(dataset, file_name, "V10", outputs_path, inputs_path)

        P = export_raster(dataset, file_name, "P", outputs_path, inputs_path, True)

        PB = export_raster(dataset, file_name, "PB", outputs_path, inputs_path, True)

        QVAPOR = export_raster(dataset, file_name, "QVAPOR", outputs_path, inputs_path, True)

        WS10m = calcWS10m(U10, V10, inputs_path)

        WS2m = calcWS2m(WS10m, inputs_path)

        RH = calcRH(T2, P, PB, QVAPOR, inputs_path)

        dataset.close()

    return True



def calcWS10m(U10, V10, inputs_path):


    for index in range(0,len(os.listdir(U10))):

        with rasterio.open(os.path.join(U10,os.listdir(U10)[index])) as src_u10:
            u10 = src_u10.read(1)
        
            transform = src_u10.transform
            crs = src_u10.crs

        with rasterio.open(os.path.join(V10,os.listdir(V10)[index])) as src_v10:
            v10 = src_v10.read(1)

        print(f"Calculated WS10m")

        WS10m = np.sqrt(u10**2 + v10**2)

        parent_dir = os.path.dirname(U10)

        if not os.path.exists(os.path.join(parent_dir, 'WS10m')):
            os.makedirs(os.path.join(parent_dir, 'WS10m'))

        file_name = os.path.join(U10,os.listdir(U10)[index]).replace("U10","WS10m")

        with rasterio.open(
            file_name,
            'w',
            driver='GTiff',
            height=WS10m.shape[0],
            width=WS10m.shape[1],
            count=1,
            dtype=WS10m.dtype,
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(WS10m, 1)

        print(f"Raster {file_name} created successfully")

        generate_image(file_name, search_csv(os.path.join(os.path.join(inputs_path, "data"), "ranges")), os.path.join(inputs_path, "data"), os.path.join(os.path.join(inputs_path, "shapefile"), "limites_municipales_2001", "limite_municipal_2001.shp"))

    return U10.replace("U10","WS10m")

def calcWS2m(WS10m, inputs_path):

    for index in range(0,len(os.listdir(WS10m))):

        with rasterio.open(os.path.join(WS10m,os.listdir(WS10m)[index]))  as src_ws10m:
            ws10m = src_ws10m.read(1)
        
            transform = src_ws10m.transform
            crs = src_ws10m.crs

        print(f"Calculated WS2m")

        z = 10

        WS2m = ws10m * (4.87 / (np.log(67.8 * z - 5.42)))

        parent_dir = os.path.dirname(WS10m)

        if not os.path.exists(os.path.join(parent_dir, 'WS2m')):
            os.makedirs(os.path.join(parent_dir, 'WS2m'))

        file_name = os.path.join(WS10m,os.listdir(WS10m)[index]).replace("WS10m","WS2m")

        with rasterio.open(
            file_name,
            'w',
            driver='GTiff',
            height=WS2m.shape[0],
            width=WS2m.shape[1],
            count=1,
            dtype=WS2m.dtype,
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(WS2m, 1)

        print(f"Raster {file_name} created successfully")

        generate_image(file_name, search_csv(os.path.join(os.path.join(inputs_path, "data"), "ranges")), os.path.join(inputs_path, "data"), os.path.join(os.path.join(inputs_path, "shapefile"), "limites_municipales_2001", "limite_municipal_2001.shp"))

    return WS10m.replace("WS10m","WS2m")


def calcRH(T2, P, PB, Q, inputs_path):


    for index in range(0,len(os.listdir(T2))):

        with rasterio.open(os.path.join(T2,os.listdir(T2)[index])) as src_t2:
            t2 = src_t2.read(1)
        
            transform = src_t2.transform
            crs = src_t2.crs

        with rasterio.open(os.path.join(P,os.listdir(P)[index])) as src_p:
            p = src_p.read(1)

        with rasterio.open(os.path.join(PB,os.listdir(PB)[index])) as src_pb:
            pb = src_pb.read(1)

        with rasterio.open(os.path.join(Q,os.listdir(Q)[index])) as src_q:
            q = src_q.read(1)

        print(f"Calculated RH")

        # Calcula la presión total (Ptot)
        Ptot = p + pb

        # Calcula la temperatura en grados Celsius (TC)
        TC = t2 - 273.15

        # Calcula la presión de vapor de agua (es)
        es = 6.1094 * np.exp(17.625) * (TC / (TC + 243.04))

        wr = 0.622 * (es / (Ptot / 100 - es))

        RH = (q/wr) * 100


        parent_dir = os.path.dirname(T2)

        if not os.path.exists(os.path.join(parent_dir, 'RH')):
            os.makedirs(os.path.join(parent_dir, 'RH'))

        file_name = os.path.join(T2,os.listdir(T2)[index]).replace("T2","RH")

        with rasterio.open(
            file_name,
            'w',
            driver='GTiff',
            height=RH.shape[0],
            width=RH.shape[1],
            count=1,
            dtype=RH.dtype,
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(RH, 1)
        
        print(f"Raster {file_name} created successfully")

        generate_image(file_name, search_csv(os.path.join(os.path.join(inputs_path, "data"), "ranges")), os.path.join(inputs_path, "data"), os.path.join(os.path.join(inputs_path, "shapefile"), "limites_municipales_2001", "limite_municipal_2001.shp"))

    return T2.replace("T2","RH")


def search_csv(ranges_path, varname):

    csvs = [os.path.join(ranges_path, file) for file in os.listdir(ranges_path)]

    def contains_keyword(file_name, keyword):
        return file_name.startswith(keyword)

    filtered_files = [file for file in csvs if contains_keyword(os.path.basename(file), varname)]

    if not filtered_files:
        filtered_files.append(os.path.join(ranges_path, "ranges_Default.csv"))

    return filtered_files