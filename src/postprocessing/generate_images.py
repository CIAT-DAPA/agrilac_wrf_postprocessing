import rasterio
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os
import geopandas as gpd
from datetime import datetime, timedelta
import numpy as np

def generate_image(raster_path, csv_path, data_path, shapefile_path=None):
    matplotlib.use('Agg')
    # Definir la ruta del logo y la ruta de guardado del PNG
    logo_path = os.path.join(data_path, "instituteLogo.jpg")
    png_file = os.path.join(os.path.dirname(raster_path), os.path.basename(raster_path).replace(".tif", "_image.png"))
    
    date = os.path.basename(raster_path).split("_")[1].split(".")[0]
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    new_date_obj = date_obj + timedelta(days=1)
    new_date_str = new_date_obj.strftime("%Y-%m-%d")
    csv_title = os.path.basename(csv_path).split("_")[1].replace(".csv", "")

    # Leer los rangos de colores desde el CSV
    color_ranges = pd.read_csv(csv_path)
    
    with rasterio.open(raster_path) as src:
        band = src.read(1)
        raster_bounds = src.bounds
        raster_crs = src.crs

    if 'season' in color_ranges.columns:
        current_date = datetime.now()
        current_season = determine_season(current_date)
        filtered_ranges = color_ranges[color_ranges['season'] == current_season]
    else:
        filtered_ranges = color_ranges

    min_vals = filtered_ranges['min'].astype(float).tolist()
    max_vals = filtered_ranges['max'].astype(float).tolist()
    cmap_colors = filtered_ranges['color'].tolist()

    # Crear los límites y colores para el mapa de colores
    boundaries = max_vals
    boundaries.insert(0, min_vals[0])
    cmap = LinearSegmentedColormap.from_list('custom_cmap', cmap_colors)
    norm = BoundaryNorm(boundaries, cmap.N)

    title = f"CENAOS/WRF {csv_title}\ndesde {date} hasta {new_date_str}"

    # Configurar la figura de Matplotlib con tamaño personalizado
    fig, ax = plt.subplots(figsize=(14, 10))

    alpha = 0.8
    interpolation = 'nearest'
    # Mostrar el mapa de colores
    im = ax.imshow(band, cmap=cmap, norm=norm, extent=[raster_bounds.left, raster_bounds.right, raster_bounds.bottom, raster_bounds.top], alpha=alpha, interpolation=interpolation)

    # Añadir el shapefile si se proporciona
    if shapefile_path and os.path.exists(shapefile_path):
        gdf = gpd.read_file(shapefile_path)
        gdf = gdf.to_crs(raster_crs)  # Reproyectar al CRS del raster
        gdf.plot(ax=ax, facecolor='none', edgecolor='black')

    # Añadir título
    ax.set_title(title, fontsize=18)

    # Añadir etiquetas a los ejes
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)

    # Añadir logo en posición absoluta
    if os.path.exists(logo_path):
        logo = plt.imread(logo_path)
        imagebox = OffsetImage(logo, zoom=0.15)
        ab = AnnotationBbox(imagebox, (0.85, 0.1), frameon=False, xycoords='axes fraction')
        ax.add_artist(ab)

    # Añadir barra de colores (colorbar) abajo a la izquierda
    cbar = fig.colorbar(im, ticks=boundaries, orientation='horizontal', boundaries=boundaries, pad=0.1, aspect=25, shrink=0.75, fraction=0.05)
    cbar.set_label(csv_title, fontsize=12)
    cbar.ax.tick_params(labelsize=10, length=5)  # Ajusta el tamaño de las etiquetas y los ticks
    cbar.ax.set_xticklabels([str(int(b)) for b in boundaries], rotation=45, ha='right')  # Rota las etiquetas si es necesario

    # Guardar la visualización como un archivo PNG
    plt.savefig(png_file, bbox_inches='tight', dpi=300)
    plt.close()  # Cerrar la figura para liberar recursos de memoria

    print(f'Imagen procesada guardada en: {png_file}')

def determine_season(date):
    # Definir los rangos de fechas para cada temporada
    season1_start = datetime(date.year, 1, 1)
    season1_end = datetime(date.year, 6, 30)
    season2_start = datetime(date.year, 7, 1)
    season2_end = datetime(date.year, 12, 31)
    
    # Determinar la temporada basada en la fecha
    if season1_start <= date <= season1_end:
        return 1
    elif season2_start <= date <= season2_end:
        return 2
    else:
        return None
