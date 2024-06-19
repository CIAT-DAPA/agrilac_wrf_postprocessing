import rasterio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def generate_image(raster_path, csv, variable, data_path):
    # Definir la ruta del logo y la ruta de guardado del PNG
    logo_path = os.path.join(data_path, "instituteLogo.jpg")
    png_file = os.path.join(os.path.dirname(raster_path), os.path.basename(raster_path).replace(".tif", "_image.png"))
    date = os.path.basename(raster_path).split("_")[1].split(".")[0]

    title = f"Precipitación en mm {date}"  # Título que deseas agregar

    with rasterio.open(raster_path) as src:
        # Leer la banda única
        band = src.read(1)
    
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

        # Ajustar tamaño de la imagen original
        img_width, img_height = img.size
        new_img_width = img_width * 2
        new_img_height = img_height * 2
        img = img.resize((new_img_width, new_img_height))

        # Obtener min y max valores
        min_val, max_val = np.nanmin(band), np.nanmax(band)

        # Escala de colores (escala)
        scale_width = 40
        scale_height = img.height - 300  # Dejar espacio para el título y el logo
        if scale_height < 0:
            scale_height = img.height // 2  # Asegurarse de que la altura de la escala sea válida
        scale_x = 50  # Margen desde la izquierda
        scale_y = img.height - scale_height - 50  # Margen desde la parte inferior
        scale = Image.new('RGBA', (scale_width, scale_height), (255, 255, 255, 255))
        scale_draw = ImageDraw.Draw(scale)

        # Generar gradiente de colores para temperatura
        for i in range(scale_height):
            ratio = i / scale_height
            color = (int(255 * ratio), 0, int(255 * (1 - ratio)), 255)  # Gradiente de azul (frío) a rojo (caliente)
            scale_draw.line([(0, i), (scale_width, i)], fill=color)

        img.paste(scale, (scale_x, scale_y))

        # Agregar valores de la escala
        font_scale = ImageFont.truetype("arial.ttf", 10)
        draw = ImageDraw.Draw(img)
        draw.text((scale_x + scale_width + 10, scale_y - 5), f"{min_val:.2f}", font=font_scale, fill="black")
        draw.text((scale_x + scale_width + 10, scale_y + scale_height - 10), f"{max_val:.2f}", font=font_scale, fill="black")

        # Agregar título
        font_title = ImageFont.truetype("arial.ttf", 30)
        text_bbox = draw.textbbox((0, 0), title, font=font_title)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (img.width - text_width) // 2
        text_y = 10  # Margen desde la parte superior
        draw.text((text_x, text_y), title, font=font_title, fill="black")

        # Agregar logo
        logo = Image.open(logo_path).convert("RGBA")
        logo_width, logo_height = logo.size
        logo = logo.resize((int(logo_width * 0.5), int(logo_height * 0.5)))  # Redimensionar el logo
        logo_width, logo_height = logo.size  # Recalcular tamaño después del redimensionamiento
        logo_x = img.width - logo_width - 20  # Margen desde el borde derecho
        logo_y = img.height - logo_height - 20  # Margen desde el borde inferior
        img.paste(logo, (logo_x, logo_y), logo)
    
        # Guardar la imagen como PNG
        img.save(png_file)
    
    print(f'Imagen procesada guardada en: {png_file}')
