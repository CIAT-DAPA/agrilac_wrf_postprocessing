import rasterio
import numpy as np
from PIL import Image
 
tiff_file = './outputs/wrfout_d02_2017-08-15_00 00 00.nc/HGT/HGT_2017-08-15.tif'
png_file = './hola.png'



def generate_image(raster_path, csv):

    with rasterio.open(raster_path) as src:
        # Leer la banda única
        band = src.read(1)
    
        # Crear una máscara para valores entre 800 y 900
        mask_red = (band > 800) & (band < 900)
    
        # Crear una máscara para identificar píxeles cero o NaN
        mask_nan = np.isnan(band)
        mask_zero = (band == 0)
        mask_white = mask_nan | mask_zero
    
        # Crear la imagen RGBA
        rgba = np.zeros((src.height, src.width, 4), dtype=np.uint8)
    
        # Asignar colores según las máscaras
        rgba[:, :, 0] = 0    # Canal rojo (inicialmente azul)
        rgba[:, :, 1] = 0    # Canal verde (inicialmente azul)
        rgba[:, :, 2] = 255  # Canal azul (constante, azul)
        rgba[:, :, 3] = 255  # Canal alfa (opaco inicialmente)
    
        # Asignar rojo a los píxeles en el rango deseado
        rgba[mask_red, 0] = 255  # Canal rojo a 255 (rojo)
        rgba[mask_red, 1] = 0    # Canal verde a 0 (rojo)
        rgba[mask_red, 2] = 0    # Canal azul a 0 (rojo)
    
        # Asignar blanco a los píxeles con valor cero o NaN
        rgba[mask_white, :] = 255  # Todos los canales a 255 (blanco)
    
        # Convertir a formato de imagen PIL
        img = Image.fromarray(rgba, 'RGBA')
    
        # Guardar la imagen como PNG
        img.save(png_file)
    
    print(f'Imagen procesada guardada en: {png_file}')