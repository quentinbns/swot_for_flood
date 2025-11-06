# swot_for_flood

Python package for Surface Water and Ocean Topography (SWOT) data processing for flood applications. The package provides tools to:
- Download SWOT High Rate data (mostly PIXC) from the Earthdata server;
- Rasterize SWOT data to create PIXC raster;
- Process rasters to analyze a flood event and extract the flood extent;
- Visualize SWOT data and flood extent.


This package is associated with the paper: 
- Q. Bonassies, C. Fatras, S. Pena-Luque, P. Dubois, A. Piacentini, L. Cassan, S. Ricci, T.-H. Nguyen (2026). A comprehensive study of Surface Water and Ocean Topography Pixel Cloud data for flood extent extraction. https://doi.org/10.1016/j.rse.2025.115101 

The graphical abstract is shown below:
![[graphical_abstract.jpg]](graphical_abstract.jpg)
The subplots are generated with this library.

The data used in the paper is available on Zenodo: 10.5281/zenodo.15848842


## Dependencies
- numpy
- pandas
- geopandas
- rasterio
- rioxarray
- shapely
- matplotlib
- seaborn
- eomaps
- cartopy
- xarray
- numba
- earthaccess

