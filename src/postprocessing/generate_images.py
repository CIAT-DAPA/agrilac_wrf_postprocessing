import rasterio
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os
import geopandas as gpd
from datetime import datetime, timedelta
import numpy as np


def generate_image(raster_path, csv_path, data_path, shapefile_path=None):
    # Definir la ruta del logo y la ruta de guardado del PNG
    logo_path = os.path.join(data_path, "instituteLogo.jpg")
    png_file = os.path.join(os.path.dirname(raster_path), os.path.basename(raster_path).replace(".tif", "_image.png"))
    
    date = os.path.basename(raster_path).split("_")[1].split(".")[0]
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    # Sumar un día
    new_date_obj = date_obj + timedelta(days=1)

    # Convertir el objeto datetime de nuevo a string
    new_date_str = new_date_obj.strftime("%Y-%m-%d")

    csv_title = os.path.basename(csv_path).split("_")[1].replace(".csv", "")

    # Leer los rangos de colores desde el CSV
    color_ranges = pd.read_csv(csv_path)
    
    with rasterio.open(raster_path) as src:
        # Leer la primera banda como un arreglo numpy
        band = src.read(1)
        raster_bounds = src.bounds
        raster_crs = src.crs
        #
        
        # Obtener los valores mínimo y máximo del raster
        raster_min = np.nanmin(band)
        raster_max = np.nanmax(band)


    # Filtrar el DataFrame de color para incluir solo los rangos dentro del rango del raster
    filtered_color_ranges = color_ranges[(color_ranges['min'] <= raster_max) & (color_ranges['max'] >= raster_min)]
    min_vals = filtered_color_ranges['min'].astype(float).tolist()
    max_vals = filtered_color_ranges['max'].astype(float).tolist()
    cmap_colors = filtered_color_ranges['color'].tolist()

    # Crear los límites y colores para el mapa de colores
    boundaries = min_vals + [max_vals[-1]]  # El valor máximo final para cerrar el último rango
    cmap = LinearSegmentedColormap.from_list('custom_cmap', cmap_colors)

    title = f"CENAOS/WRF {csv_title} desde {date} hasta {new_date_str}"  # Título que deseas agregar

    # Configurar la figura de Matplotlib con tamaño personalizado
    fig, ax = plt.subplots(figsize=(12, 8))

    # Mostrar el mapa de colores
    im = ax.imshow(band, cmap=cmap, extent=[raster_bounds.left, raster_bounds.right, raster_bounds.bottom, raster_bounds.top])

    # Añadir el shapefile si se proporciona
    if shapefile_path and os.path.exists(shapefile_path):
        gdf = gpd.read_file(shapefile_path)
        gdf = gdf.to_crs(raster_crs)  # Reproyectar al CRS del raster
        gdf.plot(ax=ax, facecolor='none', edgecolor='black')

    # Añadir título
    ax.set_title(title, fontsize=20)

    # Añadir logo en posición absoluta
    if os.path.exists(logo_path):
        logo = plt.imread(logo_path)
        imagebox = OffsetImage(logo, zoom=0.2)
        ab = AnnotationBbox(imagebox, (0.87, 0.11), frameon=False, xycoords='axes fraction')  # Coordenadas fraccionarias del eje (0.87, 0.11)
        ax.add_artist(ab)

    # Añadir barra de colores (colorbar) abajo a la izquierda
    cbar = fig.colorbar(im, ax=ax, orientation='horizontal', pad=0.1, aspect=30, fraction=0.02)
    cbar.set_label(csv_title, fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    # Guardar la visualización como un archivo PNG
    plt.savefig(png_file, bbox_inches='tight')
    plt.close()  # Cerrar la figura para liberar recursos de memoria

    print(f'Imagen procesada guardada en: {png_file}')