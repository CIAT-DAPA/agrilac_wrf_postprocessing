import os
import netCDF4 as nc
import numpy as np
import rasterio as rio
from rasterio.transform import from_origin
from export_average import export_raster
import rasterio
from datetime import datetime, timedelta


def extract_data(path):

    # Filtrar solo los archivos
    nc_files = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.nc')]

    for file in nc_files:

        file_name = os.path.basename(file)
        print(f"Procesando el archivo: {file_name}")

        dataset = nc.Dataset(file)

        xtime = dataset.variables['XTIME'][:]
        start_date_str = dataset.START_DATE

        T2 = export_raster(dataset, file_name, "T2")

        RAINNC = export_raster(dataset, file_name, "RAINNC")
        
        HGT = export_raster(dataset, file_name, "HGT")
        
        SWDOWN = export_raster(dataset, file_name, "SWDOWN")

        U10 = export_raster(dataset, file_name, "U10")
        
        V10 = export_raster(dataset, file_name, "V10")

        P = export_raster(dataset, file_name, "P", True)

        PB = export_raster(dataset, file_name, "PB", True)

        QVAPOR = export_raster(dataset, file_name, "QVAPOR", True)

        WS10m = calcWS10m(U10, V10, xtime, start_date_str)

        WS2m = calcWS2m(WS10m, xtime, start_date_str)

        RH = calcRH(T2, P, PB, QVAPOR, xtime, start_date_str)

        dataset.close()



def calcWS10m(U10, V10, xtime, start_date):

    start_datetime = datetime.strptime(start_date, '%Y-%m-%d_%H:%M:%S')

    for index in range(0,len(os.listdir(U10))):

        date = start_datetime + timedelta(minutes=int(xtime[index]))

        date = date.strftime('%Y-%m-%d')

        with rasterio.open(os.listdir(U10)[index]) as src_u10:
            u10 = src_u10.read(1)
        
            transform = src_u10.transform
            crs = src_u10.crs

        with rasterio.open(os.listdir(V10)[index]) as src_v10:
            v10 = src_v10.read(1)

        print(f"Calculated WS10m")

        WS10m = np.sqrt(u10**2 + v10**2)

        parent_dir = os.path.dirname(U10)

        if not os.path.exists(os.path.join(parent_dir, 'WS10m')):
            os.makedirs(os.path.join(parent_dir, 'WS10m'))

        file_name = os.path.join(U10.replace("U10","WS10m"), f'WS10m_{date}.tif')

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

    return U10.replace("U10","WS10m")

def calcWS2m(WS10m, xtime, start_date):

    start_datetime = datetime.strptime(start_date, '%Y-%m-%d_%H:%M:%S')

    for index in range(0,len(os.listdir(WS10m))):

        date = start_datetime + timedelta(minutes=int(xtime[index]))

        date = date.strftime('%Y-%m-%d')

        with rasterio.open(os.listdir(WS10m)[index])  as src_ws10m:
            ws10m = src_ws10m.read(1)
        
            transform = src_ws10m.transform
            crs = src_ws10m.crs

        print(f"Calculated WS2m")

        z = 10

        WS2m = ws10m * (4.87 / (np.log(67.8 * z - 5.42)))

        parent_dir = os.path.dirname(WS10m)

        if not os.path.exists(os.path.join(parent_dir, 'WS2m')):
            os.makedirs(os.path.join(parent_dir, 'WS2m'))

        file_name = os.path.join(WS10m.replace("WS10m","WS2m"), f'WS2m_{date}.tif')

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

    return WS10m.replace("WS10m","WS2m")


def calcRH(T2, P, PB, Q, xtime, start_date):

    start_datetime = datetime.strptime(start_date, '%Y-%m-%d_%H:%M:%S')

    for index in range(0,len(os.listdir(T2))):

        date = start_datetime + timedelta(minutes=int(xtime[index]))

        date = date.strftime('%Y-%m-%d')

        with rasterio.open(os.listdir(T2)[index]) as src_t2:
            t2 = src_t2.read(1)
        
            transform = src_t2.transform
            crs = src_t2.crs

        with rasterio.open(os.listdir(P)[index]) as src_p:
            p = src_p.read(1)

        with rasterio.open(os.listdir(PB)[index]) as src_pb:
            pb = src_pb.read(1)

        with rasterio.open(os.listdir(Q)[index]) as src_q:
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

        file_name = os.path.join(T2.replace("T2","RH"), f'RH_{date}.tif')

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

    return T2.replace("T2","RH")


extract_data("D:\\Code\\Honduras\\Docker\\postprocessing\\files")