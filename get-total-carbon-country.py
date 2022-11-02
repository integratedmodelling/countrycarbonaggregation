

import os
import geopandas as gpd
import rasterio
import rasterio.mask
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


"""This is the folder location of the raster files"""
# Note: the file name structure must be vcs_YYYY_global_300m.tif'
path = r"\\akif.internal\public\veg_c_storage_rawdata"

"""This is the file location of the vector global layer"""
globalmap = r"\\akif.internal\public\z_resources\im-wb\2015_gaul_dataset_mod_2015_gaul_dataset_gdba0000000b.shp"


def getrasterfiles(path):
    """Get a list of the raster files inside the folder"""
    File_list = []
    for file in os.listdir(path):
        if ".tif" in file:
            if file not in File_list:
                File_list.append(file)
        else:
            pass
    return File_list

def globaldataframe(globalmap):
    """Create dataframe out of the vector data"""
    gdf = gpd.read_file(globalmap)
    return gdf

def carboncalculator(path, File_list, gdf):
    """Iterate over the raster files, mask them by each country, get the total carbon values
     and create the results on a dataframe"""

    """We set ourselves in the folder with the rasters"""
    os.chdir(path)

    """Iterate the rasters"""
    for file in File_list[:]:
        """Take the year of the file"""
        file_year = str(file[4:8])
        print("\r", "We are working with the file {} from the year {}".format(file, file_year), end="")

        """Create a list of the carbon values"""
        carbon_values = []

        """Open the raster"""
        with rasterio.open(file) as raster_file:

            """Iterate on the gdf"""
            for row_index, row in gdf.iterrows(): # gdf.loc[0:1].iterrows():
                geo_row = gpd.GeoSeries(row['geometry'])

                """Do the masking"""
                out_image, out_transform = rasterio.mask.mask(raster_file, geo_row, crop=True)

                """Sum the values ignoring the nan values"""
                carbon_total = np.nansum(out_image) # nansum treats nan values as 0, we have to do this since with sum we get as result nan

                """Append the value to the list"""
                carbon_values.append(carbon_total)

                print("\r", "the country {} is finished".format(row["ADM0_NAME"]), end="") #with this method we dont accumulate messages
                
        print("\r", "Finished calculating {} year raster".format(file_year), end="")

        """Transform the list into a dataframe with the header of the year"""
        carbon_values_s = pd.DataFrame(carbon_values, columns = [file_year])

        """Acumulate the values into a single dataframe"""
        carbon_values_df = carbon_values_df.join(carbon_values_s)
    return carbon_values_df


def outputdataframe(gdf, carbon_values_df):
    """Prepare the dataframe for the final table"""   
    df_final = pd.DataFrame(gdf.drop(columns='geometry'))
    df_final = df_final.drop(["STATUS", "DISP_AREA", "ADM0_CODE", "STR0_YEAR", "EXP0_YEAR", "Shape_Leng", "ISO3166_1_", "ISO3166__1", "Shape_Le_1", "Shape_Area"], axis = 1)

    """Append the dataframe to the final dataframe"""
    df_final = df_final.join(carbon_values_df)
        
    """Export the result"""
    df_final.to_csv("total_carbon.csv")


