import rasterio
from rasterio.mask import mask
import geopandas as gpd
import os
from shapely.geometry import mapping
import numpy as np


def cut_rasters(raster_filename, shp_path):

    # Abrir el shapefile
    shapefile = gpd.read_file(shp_path)


    # Convertir el shapefile a una lista de geometrías
    shapes = [feature["geometry"] for feature in shapefile.__geo_interface__["features"]]

    # Abrir el raster
    with rasterio.open(raster_filename) as src:
        

        if shapefile.crs != src.crs:
            shapefile = shapefile.to_crs(src.crs)
        
        # Convertir el shapefile a una lista de geometrías
        shapes = [mapping(geom) for geom in shapefile.geometry]

        # Recortar el raster con el shapefile
        out_image, out_transform = mask(src, shapes, crop=True)
        if src.nodata is not None:
            nodata = src.nodata
            out_image[out_image == nodata] = np.nan
        zero_mask = (out_image == 0)
        if np.any(zero_mask):
            print("Hay valores cero en los datos recortados. Reemplazando con np.nan.")
            out_image[zero_mask] = np.nan
        out_meta = src.meta.copy()

        # Actualizar los metadatos del raster recortado
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        # Guardar el raster recortado
        with rasterio.open(raster_filename.replace(os.path.basename(raster_filename), os.path.basename(raster_filename).replace("_raster","")), "w", **out_meta) as dest:
            dest.write(out_image)

    os.remove(raster_filename)
