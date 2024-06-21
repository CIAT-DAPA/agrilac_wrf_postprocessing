# WRF Postprocessing Module

![GitHub release (latest by date)](https://img.shields.io/github/v/release/CIAT-DAPA/agrilac_wrf_postprocessing) ![](https://img.shields.io/github/v/tag/CIAT-DAPA/agrilac_wrf_postprocessing)

This repository contains a Python package designed for postprocessing outputs from the WRF model within the context of the Agrilac project.

## Features

- Extract variables from WRF model outputs in NetCDF format.
- Convert extracted variables into daily raster images.
- Generate PNG images from the transformed raster data for visualization and analysis.

## Prerequisites

- Python >=3.9
- Dependencies listed in requirements.txt

## Configure DEV Enviroment

You should create a env to run the code and install the requeriments. Run the following commands in the prompt

```bash
pip install virtualenv
venv env
pip install -r requirements.txt
```

## Installation

To use this package as a library in your Python projects, install it via pip:

```bash
pip install git+https://github.com/CIAT-DAPA/agrilac_wrf_postprocessing
```

## Configuration

Configure input and output paths before running the script:

- -i, --inputs: Path to directory containing WRF model output NetCDF files. Within the path you should have 3 folders **wrf/** where the NedCDF files will be, **shapefile/** where the shapefiles will be to divide the map and **data/** where the logo will be and the folder **ranges/** with the color ranges of each variable.

- -o, --outputs: Path where processed raster and PNG files will be saved.

> [!NOTE]
> You can copy the content of the **data** folder found in this repository into the input path that you will pass as a parameter to follow the folder format and add the **wrf** folder with the NedCDF files.

## Usage

Run the script wrf_postprocessing with the following parameters:

```bash
wrf_postprocessing -i "/path/to/input/" -o "/path/to/output/"
```

## Parameters

-i, --inputs: Path to directory containing WRF model output NetCDF files.
-o, --outputs: Path where processed raster and PNG files will be saved.

## Example

```bash
wrf_postprocessing -i "/home/user/data/WRF_outputs" -o "/home/user/data/processed_outputs"
```

This command processes NetCDF files from /home/user/data/WRF_outputs, converts them into daily raster images, and saves the resulting PNG files in /home/user/data/processed_outputs.
