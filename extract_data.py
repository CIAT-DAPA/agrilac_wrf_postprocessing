import os
import netCDF4 as nc
import numpy as np
import rasterio as rio
from rasterio.transform import from_origin
from export_average import export_raster


def extract_data(path):

    # Filtrar solo los archivos
    nc_files = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.nc')]

    for file in nc_files:

        file_name = os.path.basename(file)
        print(f"Procesando el archivo: {file_name}")

        dataset = nc.Dataset(file)


        T2 = export_raster(dataset, file_name, "T2")

        RAINNC = export_raster(dataset, file_name, "RAINNC")
        
        HGT = export_raster(dataset, file_name, "HGT")
        
        SWDOWN = export_raster(dataset, file_name, "SWDOWN")

        U10 = export_raster(dataset, file_name, "U10")
        
        V10 = export_raster(dataset, file_name, "V10")

        WS10m = calcWS10m(U10, V10)

        WS2m = calcWS2m(WS10m)

        dataset.close()



def calcWS10m(U10, V10):

    WS10m = np.sqrt(U10**2 + V10**2)

    return WS10m

def calcWS2m(WS10m):

    z = 10

    WS2m = WS10m * (4.87 / (np.log(67.8 * z - 5.42)))

    return WS2m


def calcRH(T2, P, PB, Q):

    # Calcula la presión total (Ptot)
    Ptot = P + PB

    # Calcula la temperatura en grados Celsius (TC)
    TC = T2 - 273.15

    # Calcula la presión de vapor de agua (es)
    es = 6.1094 * np.exp(17.625) * (TC / (TC + 243.04))

    wr = 0.622 * (es / (Ptot / 100 - es))

    RH = (Q/wr) * 100

    return RH


extract_data("D:\\Code\\Honduras\\Docker\\postprocessing\\files")