from setuptools import setup, find_packages

setup(
    name="agrilac_wrf_postprocessing",
    version='v0.0.7',
    author="stevensotelo",
    author_email="h.sotelo@cgiar.com",
    description="Postprocessing wrf outputs",
    url="https://github.com/CIAT-DAPA/agrilac_wrf_postprocessing",
    download_url="https://github.com/CIAT-DAPA/agrilac_wrf_postprocessing",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    keywords='postprocessing wrf rasters',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'wrf_postprocessing=postprocessing.main:main',
        ],
    },
    install_requires=[
        "certifi==2024.6.2",
        "cftime==1.6.4",
        "click==8.1.7",
        "click-plugins==1.1.1",
        "cligj==0.7.2",
        "colorama==0.4.6",
        "contourpy==1.1.1",
        "cycler==0.12.1",
        "fiona==1.9.6",
        "fonttools==4.53.0",
        "geopandas==0.13.2",
        "kiwisolver==1.4.5",
        "matplotlib==3.9.0",
        "netCDF4==1.7.1",
        "numpy==2.0.0",
        "packaging==24.1",
        "pandas==2.2.2",
        "pillow==10.3.0",
        "pyparsing==3.1.2",
        "pyproj==3.6.1",
        "python-dateutil==2.9.0.post0",
        "pytz==2024.1",
        "rasterio==1.3.10",
        "shapely==2.0.4",
        "six==1.16.0",
        "snuggs==1.4.7",
        "tzdata==2024.1"
    ]
)