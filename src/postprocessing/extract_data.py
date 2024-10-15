import os
import netCDF4 as nc
import numpy as np
import rasterio as rio
from rasterio.transform import from_origin, xy
import xarray as xr
from .export_average import export_raster
from .generate_images import generate_image
import rasterio
import math
from datetime import datetime, timedelta


def extract_data(inputs_path, outputs_path):

    
    wrf_inputs_path = os.path.join(inputs_path, "wrf")

    # Filtrar solo los archivos
    nc_files = [os.path.join(wrf_inputs_path, file) for file in os.listdir(wrf_inputs_path)]


    for file in nc_files:

        file_name = os.path.basename(file)
        print(f"Procesando el archivo: {file_name}")

        dataset = xr.open_dataset(file, decode_times=False)

        RAIN = export_raster(dataset, file_name, "RAIN", outputs_path, inputs_path)

        T2 = export_raster(dataset, file_name, "T2", outputs_path, inputs_path)

        HGT = export_raster(dataset, file_name, "HGT", outputs_path, inputs_path)
        
        SWDOWN = export_raster(dataset, file_name, "SWDOWN", outputs_path, inputs_path)

        U10 = export_raster(dataset, file_name, "U10", outputs_path, inputs_path)
        
        V10 = export_raster(dataset, file_name, "V10", outputs_path, inputs_path)

        P = export_raster(dataset, file_name, "P", outputs_path, inputs_path, True)

        PB = export_raster(dataset, file_name, "PB", outputs_path, inputs_path, True)

        QVAPOR = export_raster(dataset, file_name, "QVAPOR", outputs_path, inputs_path, True)

        SMOIS = export_raster(dataset, file_name, "SMOIS", outputs_path, inputs_path, True)

        WS10m = calcWS10m(U10, V10, inputs_path)

        WS2m = calcWS2m(WS10m, inputs_path)

        RH = calcRH(T2, P, PB, QVAPOR, inputs_path)

        ET0 = calcET0(T2, RH, WS2m, SWDOWN, inputs_path)

        # dataset.close()

    return True



def calcWS10m(U10, V10, inputs_path):

    tif_U10_files = [file for file in os.listdir(U10) if file.endswith('.tif')]
    tif_V10_files = [file for file in os.listdir(V10) if file.endswith('.tif')]

    for index in range(0,len(tif_U10_files)):

        with rasterio.open(os.path.join(U10,tif_U10_files[index])) as src_u10:
            u10 = src_u10.read(1)
        
            transform = src_u10.transform
            crs = src_u10.crs

        with rasterio.open(os.path.join(V10,tif_V10_files[index])) as src_v10:
            v10 = src_v10.read(1)

        print(f"Calculated WS10m")

        WS10m = np.sqrt(u10**2 + v10**2)

        parent_dir = os.path.dirname(U10)

        if not os.path.exists(os.path.join(parent_dir, 'WS10m')):
            os.makedirs(os.path.join(parent_dir, 'WS10m'))

        file_name = os.path.join(U10,tif_U10_files[index]).replace("U10","WS10m")

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

        generate_image(file_name, search_csv(os.path.join(inputs_path, "data", "ranges"), "WS10m"), os.path.join(inputs_path, "data"), os.path.join(inputs_path, "shapefile", "limites_municipales", "limite_municipal.shp"))

    return U10.replace("U10","WS10m")

def calcWS2m(WS10m, inputs_path):

    tif_files = [file for file in os.listdir(WS10m) if file.endswith('.tif')]

    for index in range(0,len(tif_files)):

        with rasterio.open(os.path.join(WS10m,tif_files[index])) as src_ws10m:
            ws10m = src_ws10m.read(1)
        
            transform = src_ws10m.transform
            crs = src_ws10m.crs

        print(f"Calculated WS2m")

        z = 10

        WS2m = ws10m * (4.87 / (np.log(67.8 * z - 5.42)))

        parent_dir = os.path.dirname(WS10m)

        if not os.path.exists(os.path.join(parent_dir, 'WS2m')):
            os.makedirs(os.path.join(parent_dir, 'WS2m'))

        file_name = os.path.join(WS10m,tif_files[index]).replace("WS10m","WS2m")

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

        generate_image(file_name, search_csv(os.path.join(inputs_path, "data", "ranges"), "WS2m"), os.path.join(inputs_path, "data"), os.path.join(inputs_path, "shapefile", "limites_municipales", "limite_municipal.shp"))

    return WS10m.replace("WS10m","WS2m")


def calcRH(T2, P, PB, Q, inputs_path):

    tif_T2_files = [file for file in os.listdir(T2) if file.endswith('.tif')]
    tif_P_files = [file for file in os.listdir(P) if file.endswith('.tif')]
    tif_PB_files = [file for file in os.listdir(PB) if file.endswith('.tif')]
    tif_Q_files = [file for file in os.listdir(Q) if file.endswith('.tif')]

    for index in range(0,len(tif_T2_files)):

        with rasterio.open(os.path.join(T2,tif_T2_files[index])) as src_t2:
            t2 = src_t2.read(1)
        
            transform = src_t2.transform
            crs = src_t2.crs

        with rasterio.open(os.path.join(P,tif_P_files[index])) as src_p:
            p = src_p.read(1)

        with rasterio.open(os.path.join(PB,tif_PB_files[index])) as src_pb:
            pb = src_pb.read(1)

        with rasterio.open(os.path.join(Q,tif_Q_files[index])) as src_q:
            q = src_q.read(1)

        print(f"Calculated RH")

        # Calcula la presión total (Ptot)
        Ptot = p + pb

        # Calcula la temperatura en grados Celsius (TC)
        TC = t2

        # Calcula la presión de vapor de agua (es)
        es = 6.1094 * np.exp((17.625 * TC) / (TC + 243.04))

        wr = 0.622 * (es / (Ptot / 100 - es))

        RH = (q/wr) * 100


        parent_dir = os.path.dirname(T2)

        if not os.path.exists(os.path.join(parent_dir, 'RH')):
            os.makedirs(os.path.join(parent_dir, 'RH'))

        file_name = os.path.join(T2,tif_T2_files[index]).replace("T2","RH")

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

        generate_image(file_name, search_csv(os.path.join(inputs_path, "data", "ranges"), "RH"), os.path.join(inputs_path, "data"), os.path.join(inputs_path, "shapefile", "limites_municipales", "limite_municipal.shp"))

    return T2.replace("T2","RH")


def calcET0(T2, RH, WS2m, SWDOWN, inputs_path):

    pressure = 101.325

    dates_list = []
    doy_list = []
    yesterday = datetime.now() - timedelta(days=1)
    ndays = 10
    for i in range(ndays):
        date = yesterday - timedelta(days=i)
        year = date.strftime('%Y')
        doy = date.strftime('%j')
        date_str = year + doy
        dates_list.append(date_str)
        doy_list.append(int(doy))

    tif_T2_files = [file for file in os.listdir(T2) if file.endswith('.tif')]
    tif_RH_files = [file for file in os.listdir(RH) if file.endswith('.tif')]
    tif_WS2m_files = [file for file in os.listdir(WS2m) if file.endswith('.tif')]
    tif_SWDOWN_files = [file for file in os.listdir(SWDOWN) if file.endswith('.tif')]

    count = -1

    for index in range(0,len(tif_T2_files)):

        count = count + 1
        doy = doy_list[count]

        with rasterio.open(os.path.join(T2,tif_T2_files[index])) as src_t2:
            t2 = src_t2.read(1)
        
            transform = src_t2.transform
            crs = src_t2.crs

        rows, cols = t2.shape
        ET0 = np.empty((rows, cols))
        ET0[:] = np.nan

        with rasterio.open(os.path.join(RH,tif_RH_files[index])) as src_rh:
            rh = src_rh.read(1)
        with rasterio.open(os.path.join(SWDOWN,tif_SWDOWN_files[index])) as src_swdown:
            swdown = src_swdown.read(1)
        with rasterio.open(os.path.join(WS2m,tif_WS2m_files[index])) as src_ws2m:
            ws2m = src_ws2m.read(1)


        for i in range(rows):
        
            for j in range(cols):

                lon, latitude = xy(transform, i, j)
                   
                mytas = t2[i,j]
                myrh = rh[i,j]
                myws = ws2m[i,j]
                mysr = swdown[i,j]*0.0864  #W/m2 to MJ/m2/d
                
                # PRESION DE VAPOR A SATURACION Y ACTUAL
                es = 0.6108 * math.exp(17.27 * mytas / (mytas + 237.3))
                ea = (myrh / 100) * es
                
                # PENDIENTE DE LA CURVA DE PRESION DE VAPOR Y CONSTANTE PSICROMETRICA
                delta = 4098 * es / (mytas + 237.3) ** 2
                gamma = 0.665 * 10 ** (-3) * pressure / 0.622
                
                                
                # RADIACION SOLAR DE DIA DESPEJADO Y RADIACION EXTRATERRESTRE
                dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * doy)
                delta_s = 0.409 * math.sin(2 * math.pi / 365 * doy - 1.39)
                omega_s = math.acos(-math.tan(latitude * math.pi / 180) * math.tan(delta_s))
                Ra = (24 * 60 / math.pi) * 0.082 * dr * (omega_s * math.sin(latitude * math.pi / 180) * math.sin(delta_s) + math.cos(latitude * math.pi / 180) * math.cos(delta_s) * math.sin(omega_s))
                
                # RADIACION SOLAR NETA Y RADIACION NETA DE ONDA LARGA EMERGENTE
                Rns = 0.77 * mysr
                Rnl = 4.903 * 10 ** (-9) * ((mytas + 273.16) ** 4) * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * (mysr / Ra) - 0.35)
                
                Rn = Rns - Rnl
                G = 0 # A ESCALA DIARIA = 0
                
                # ET0
                calculatedET0 = (0.408 * delta * (Rn - G) + gamma * (900 / (mytas + 273)) * myws * (es - ea)) / (delta + gamma * (1 + 0.34 * myws))

                ET0[i][j] = calculatedET0

        print(f"Calculated ET0")

        parent_dir = os.path.dirname(T2)

        if not os.path.exists(os.path.join(parent_dir, 'ET0')):
            os.makedirs(os.path.join(parent_dir, 'ET0'))

        file_name = os.path.join(T2,tif_T2_files[index]).replace("T2","ET0")

        with rasterio.open(
            file_name,
            'w',
            driver='GTiff',
            height=ET0.shape[0],
            width=ET0.shape[1],
            count=1,
            dtype=ET0.dtype,
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(ET0, 1)

        print(f"Raster {file_name} created successfully")

        generate_image(file_name, search_csv(os.path.join(inputs_path, "data", "ranges"), "ET0"), os.path.join(inputs_path, "data"), os.path.join(inputs_path, "shapefile", "limites_municipales", "limite_municipal.shp"))

    return T2.replace("T2","ET0")


def search_csv(ranges_path, varname):

    csvs = [os.path.join(ranges_path, file) for file in os.listdir(ranges_path)]

    def contains_keyword(file_name, keyword):
        return file_name.startswith(keyword)

    filtered_files = [file for file in csvs if contains_keyword(os.path.basename(file), varname)]

    if not filtered_files:
        filtered_files.append(os.path.join(ranges_path, "ranges_Default.csv"))

    return filtered_files[0]