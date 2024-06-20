import rasterio
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os

def generate_image(raster_path, csv_path, variable, data_path):
    # Definir la ruta del logo y la ruta de guardado del PNG
    logo_path = os.path.join(data_path, "instituteLogo.jpg")
    png_file = os.path.join(os.path.dirname(raster_path), os.path.basename(raster_path).replace(".tif", "_image.png"))
    date = os.path.basename(raster_path).split("_")[1].split(".")[0]

    # Leer los rangos de colores desde el CSV
    color_ranges = pd.read_csv(csv_path)

    title = f"Precipitación en mm {date}"  # Título que deseas agregar

    with rasterio.open(raster_path) as src:
        # Leer la primera banda como un arreglo numpy
        band = src.read(1)
        raster_bounds = src.bounds

        # Crear el mapa de colores basado en los rangos del CSV con degradado
        cmap_colors = []
        for index, row in color_ranges.iterrows():
            color = row['color']
            cmap_colors.append(color)
        cmap = LinearSegmentedColormap.from_list('custom_cmap', cmap_colors)
        
        # Configurar la figura de Matplotlib con tamaño personalizado
        fig, ax = plt.subplots(figsize=(12, 8))

        # Mostrar el mapa de colores
        im = ax.imshow(band, cmap=cmap, extent=[raster_bounds.left, raster_bounds.right, raster_bounds.bottom, raster_bounds.top])

        # Añadir título
        ax.set_title(title, fontsize=20)

        # Añadir logo en posición absoluta
        if os.path.exists(logo_path):
            logo = plt.imread(logo_path)
            imagebox = OffsetImage(logo, zoom=0.2)
            ab = AnnotationBbox(imagebox, (0.87, 0.11), frameon=False, xycoords='axes fraction')  # Coordenadas fraccionarias del eje (0.95, 0.05)
            ax.add_artist(ab)

        # Añadir barra de colores (colorbar) abajo a la izquierda
        cbar = fig.colorbar(im, ax=ax, orientation='horizontal', pad=0.1, aspect=30, fraction=0.02)
        cbar.set_label('Precipitación en mm', fontsize=12)
        cbar.ax.tick_params(labelsize=10)

        # Guardar la visualización como un archivo PNG
        plt.savefig(png_file, bbox_inches='tight')
        plt.close()  # Cerrar la figura para liberar recursos de memoria

    print(f'Imagen procesada guardada en: {png_file}')

# Ejemplo de uso
generate_image('D:\\Code\\Honduras\\Docker\\postprocessing\\outputs\\wrfout_d02_2017-08-15_00 00 00.nc\\HGT\\HGT_2017-08-15.tif', 
               'D:\\Code\\Honduras\\Docker\\postprocessing\\files\\data\\test.csv',
               'HGT',
               'D:\\Code\\Honduras\\Docker\\postprocessing\\files\\data')
