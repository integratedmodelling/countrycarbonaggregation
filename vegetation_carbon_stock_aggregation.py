"""
This script performs the aggregation of global vegetation carbon stocks in Tonnes per Hectare at the country-level for the 2001-2020 period.
The result is a CSV table storing the total vegetation carbon stock in Tonnes for each country in the entire world and for each year between 2001 and 2020.

The script is structured in the following way: 
- l.19-73:   declaration of the functions used for Input/Ouput.
- l.73-133:  declaration of the function where the aggregation process is implemented.
- l.136-161: main program where the aggregation process is carried on. 
"""

import os
import geopandas as gpd
import rasterio
import rasterio.mask
import numpy as np
import pandas as pd
import math

"""
Begin of functions' declaration.
"""

"""
Input/Ouput functions.
"""

def get_raster_data(path):
    """
    get_raster_data gets the adresses of all the raster files ("*.tif") contained in the directory specified by path. Each raster file
                         corresponds to a different year.

    :param path: directory containing the raster data for the global vegetation carbon stocks at 300m resolution for each year.
    :return: a list storing the adresses of all the raster files containing the data to be aggregated by country. 
    """ 
    file_list = []
    for file in os.listdir(path):
        # Iterate over all the files in the specified directory.
        if ".tif" in file:
            # Process the file if it has a .tif format.
            address = path + file
            if address not in file_list:
                # Add the file address to the list if it had not been added before.
                file_list.append(address)
        else:
            pass
    return file_list

def load_country_polygons(file):
    """
    load_country_polygons loads a shapefile containing vector data of country borders for the entire world as a GeoDataFrame.
    
    :param file: the adress of the shapefile with the country border data.
    :return: a GeoDataFrame with country border data. 
    """
    gdf = gpd.read_file(file)
    return gdf

def export_to_csv(country_polygons, aggregated_carbon_stocks):
    """
    export_to_csv creates a DataFrame where aggregated vegetation carbon stocks are associated to each country and exports this data in CSV format. 
    
    :param country_polygons: a GeoDataFrame storing the polygons corresponding to each country for the entire world.
    :param aggregated_carbon_stocks: a DataFrame storing the aggregated carbon stock values to be associated to each country.
    :return: None. The function creates a "total_carbon_test.csv" file in the current working directory that contains the total vegetation carbon stock for each country.
    """
    
    # Create a DataFrame based on the country border GeoDataFrame and droping unnecesary information to keep only: the polygons' Id, country codes and administrative names.
    df_final = pd.DataFrame(country_polygons.drop(columns='geometry'))
    df_final = df_final.drop(["STATUS", "DISP_AREA", "ADM0_CODE", "STR0_YEAR", "EXP0_YEAR", "Shape_Leng", "ISO3166_1_", "ISO3166__1", "Shape_Le_1", "Shape_Area"], axis = 1)

    # Join the depurated country DataFrame with the aggregated vegetation carbon stocks to associate each country to its total stock.  
    df_final = df_final.join(aggregated_carbon_stocks)
        
    # Export the result to the current working directory.
    df_final.to_csv("total_carbon_test.csv")

"""
Processing function.
"""

def area_of_pixel(pixel_size, center_lat):
    """Calculate m^2 area of a wgs84 square pixel.

    Adapted from: https://gis.stackexchange.com/a/127327/2397

    Parameters:
        pixel_size (float): length of side of pixel in degrees.
        center_lat (float): latitude of the center of the pixel. Note this
            value +/- half the `pixel-size` must not exceed 90/-90 degrees
            latitude or an invalid area will be calculated.

    Returns:
        Area of square pixel of side length `pixel_size` centered at
        `center_lat` in ha.

    """
    a = 6378137  # meters
    b = 6356752.3142  # meters
    e = math.sqrt(1 - (b/a)**2)
    area_list = []
    for f in [center_lat+pixel_size/2, center_lat-pixel_size/2]:
        zm = 1 - e*math.sin(math.radians(f))
        zp = 1 + e*math.sin(math.radians(f))
        area_list.append(
            math.pi * b**2 * (
                math.log(zp/zm) / (2*e) +
                math.sin(math.radians(f)) / (zp*zm)))
    return (pixel_size / 360. * (area_list[0] - area_list[1])) * np.power(10,-4) 

def get_raster_area(out_image, out_transform, pixel_size):
        height = out_image.shape[2]
        width = out_image.shape[1]
        cols, rows = np.meshgrid(np.arange(width), np.arange(height))
        xs, ys = rasterio.transform.xy(out_transform, rows, cols)
        # longitudes= np.array(xs)
        latitudes = np.array(ys)

        real_raster_areas = np.zeros(latitudes)
        for i, latitude_array in enumerate(latitudes):
            for j, latitude in enumerate(latitude_array):
                real_raster_areas[i,j] = area_of_pixel(pixel_size, latitude)

        return real_raster_areas

def carbon_stock_aggregation(raster_files_list, country_polygons):
    """
    carbon_stock_aggregation aggregates vegetation carbon stock data in Tonnes per Hectare and with a resolution of 300m at the country level. 
                             The result of the aggregation is the total vegetation carbon stock in Tonnes for each country. Naturally, the 
                             dependence of raster tile area on the latitude is taken into account. The function iterates over the carbon stock 
                             rasters corresponding to different years.
    
    :param raster_files_list: a list containing the addresses of all the raster files that store the vegetation carbon stock data for each year.
    :country_polygons: a GeoDataFrame storing the polygons corresponding to each country for the entire world.
    :return: a DataFrame storing the aggregated vegetation carbon stocks at the country level for each year.
    """
    
    # Final DataFrame will store the aggregated carbon stocks for each country and each year. 
    aggregated_carbon_stock_df = pd.DataFrame([])
    
    for file in raster_files_list[:]:
        # Iterate over all the raster files' addresses and extract the year from the address. 
        # TODO: check if this works properly 
        filename_length = 24 # This is the number of characters in the raster file name if the convention "vcs_YYYY_global_300m.tif" is followed.
        start = len(file) - filename_length
        year_string_start = file.find("vcs_",start)
        year_string_end   = file.find("_global_300m_.tif",start)
        file_year = str( file[ year_string_start+4 : year_string_end ] )
        
        print("\r", "We are working with the file {} from the year {}".format(file, file_year), end="")

        aggregated_carbon_stock_list = [] # This list will store the results from the aggregation. 

        with rasterio.open(file) as raster_file: # Load the raster file.

            gt = raster_file.transform # Get the raster properties on a list
            pixel_size = gt[0] # 0 possition gets the x size, 4 possition gets the y size

            for row_index, row in country_polygons.iterrows(): # gdf.loc[0:1].iterrows():
                # Iterate over the country polygons to progressively calculate the total carbon stock in each one of them.
                
                geo_row = gpd.GeoSeries(row['geometry']) # This is the country's polygon geometry.

                out_image, out_transform = rasterio.mask.mask(raster_file, geo_row, crop=True) # Masks the raster over the current country.
                
                real_raster_areas = get_raster_area(out_image, out_transform, pixel_size)

                total_carbon_stock_array = real_raster_areas * out_image

                total_carbon_stock = np.nansum(total_carbon_stock_array) # Sum all the carbon stock values in the country treating NaNs as 0.0. 
                
                aggregated_carbon_stock_list.append(total_carbon_stock) # Add the aggregated stock to the list. 

                print("\r", "the country {} is finished".format(row["ADM0_NAME"]), end="") 
                
        print("Finished calculating {} year raster".format(file_year))
    
        # Transform the list to a DataFrame using the year as header.
        aggregated_carbon_stock = pd.DataFrame(aggregated_carbon_stock_list, columns = [file_year]) 

        # Merge this year's carbon stocks to the final, multi-year DataFrame.
        aggregated_carbon_stock_df = pd.merge(aggregated_carbon_stock_df, aggregated_carbon_stock, how='outer', left_index = True, right_index=True)

    return aggregated_carbon_stock_df

"""
End of functions' declaration.
"""

"""
Aggregation of vegetation carbon stock at the country level. 
"""

"""
Directory containing the raster files for the global carbon stock data at 300m resolution. This is the data to be aggregated by country.
Note that the raster filenames must have the following structure: vcs_YYYY_global_300m.tif.
"""
vcs_rasters_directory = r"\\akif.internal\public\veg_c_storage_rawdata\" # This is for Windows systems.
# vcs_rasters_directory = r"akif.internal/public/veg_c_storage_rawdata/" # This is for Unix systems.

"""
Full address of the shapefile containing the data on country borders for the entire world. This determines the country polygons 
inside which the aggregation of carbon stocks is done. 
"""
country_polygons_file = r"\\akif.internal\public\z_resources\im-wb\2015_gaul_dataset_mod_2015_gaul_dataset_gdba0000000b.shp" # This is for Windows systems.
# country_polygons_file = r"akif.internal/public/z_resources/im-wb/2015_gaul_dataset_mod_2015_gaul_dataset_gdba0000000b.shp" # This is for Unix systems.

print("Loading data.")
vcs_rasters_list = get_raster_data(vcs_rasters_directory) 
country_polygons = load_country_polygons(country_polygons_file) 
print("Data was loaded succesfully.")

print("Starting aggregation process.")
vcs_aggregated   = carbon_stock_aggregation(vcs_rasters_list, country_polygons) 
print("Aggregation of vegetation carbon stocks at the country level finished.")
export_to_csv(country_polygons, vcs_aggregated) 
print("Total vegetation carbon stocks at the country level succesfully exported.")
