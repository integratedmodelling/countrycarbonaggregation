import os
import geopandas as gpd
import rasterio
import rasterio.mask
import numpy as np
import pandas as pd
import math
import platform
from matplotlib import pyplot as plt
import seaborn as sns

def get_vcs_filenames(path):
    """
    Store the filenames of the vegetation carbon stock data for every year in a
    list.
    :param path: is the path to the data directory.
    :return: a list containing all the filenames.
    """
    file_list = []
    for file in os.listdir(path):
        # Iterate over all the files in the specified directory.
        if ".csv" in file:
            # Process the file if it has a .tif format.
            if platform.system() == "Windows":
                address = os.path.join(path, file).replace("/","\\")
            else:
                address = os.path.join(path, file).replace("\\","/")
                #build the path according the OS running the script

            if address not in file_list:
                # Add the file address to the list if it had not been added before.
                file_list.append(address)
        else:
            pass
    return file_list

def merge_vcs_all_years(vcs_files):
    """
    Merges all the vegetation carbon stock data for every year in a single
    DataFrame with the years as headers.
    :param vcs_files: a list with the paths to every vegetation carbon stock CSV
    data file.
    :return: a DataFrame with all the data merged and indexed by country index.
    """

    # Iterate over the filenames to progressively load and merge them.
    for file in vcs_files:

        # Load the file
        vcs = pd.read_csv(file)
        vcs = vcs.rename( columns={'Unnamed: 0' : "cid" } )
        try:
            vcs_df = pd.merge(vcs_df, vcs, on = ["cid"])
        except:
            vcs_df = pd.DataFrame(vcs)

    return vcs_df[sorted(vcs_df)]

def load_countries_polygon_data(countries_file):
    """
    Loads the countries' polygon data in a GeoDataFrame and removes the unneeded
    columns.
    :param countries_file: is the polygon layer with countries names and
    polygons.
    :return: the reduced countries GeoDataFrame with one column with the names
    and a second one with the geometry.
    """

    countries_polygons = gpd.read_file(countries_file)
    countries_polygons = countries_polygons[["OBJECTID","ADM0_NAME","geometry"]]
    countries_polygons = countries_polygons.rename( columns = {"OBJECTID":"cid", "ADM0_NAME":"name"})
    countries_polygons["cid"] = (countries_polygons["cid"] - 1).astype(int)
    return countries_polygons

def join_vcs_with_country(vcs_df, countries_gdf):
    """
    Joins the vegetation carbon stock DataFrame with the country names and
    polygons.
    :param vcs_df: is the DataFrame storing the vegetation carbon stock data.
    :param countries_gdf: is a GeoDataFrame containing the country names and
    geometries.
    :return: a GeoDataFrame with country names and polygons and the associated
    vegetation carbon stock in tonnes.
    """
    joined = vcs_df.merge(countries_gdf, on="cid")
    joined = joined.drop("cid",axis=1)
    print(joined)
    return joined

def vcs_differences(gdf, init_year, last_year, time_interval):
    """
    Calculates the differences in vegetation carbon stocks between evenly spaced
    years for every country.
    :param gdf: is the country-vegetation carbon stock dataset.
    :param init_year: is the initial year of the analysis.
    :param last_year: is the last year of the analyis.
    :param time_interval: is the time step for the analysis.
    :return: a GeoDataframe with data on the differences in vegetation carbon
    stock between the given years.
    """

    init_years = np.arange(init_year,last_year + 1 ,time_interval)[:-1].tolist()
    last_years  = np.arange(init_year,last_year + 1 ,time_interval)[1:].tolist()
    years = list(zip(init_years, last_years))

    diff_gdf = gdf[["name","geometry"]]
    for y0,y1 in years:
        diff_gdf[str(y1)+"-"+str(y0)] = 100*(gdf[str(y1)]-gdf[str(y0)])/gdf[str(y0)]

    return diff_gdf

def get_winners_and_losers(gdf, init_year, last_year):
    """
    Gets the top 10 winner/loser countries in terms of changes in vegetation
    carbon stock between two years.
    :param gdf: the dataset.
    :param init_year: the initial year.
    :param last_year: the last year.
    :return: a duple of Series with the names of the countries in the top 10 of
    winners and losers regarding vegetation carbon stock changes.
    """

    diff = vcs_differences(gdf, init_year, last_year, last_year - init_year)

    winners = diff[ diff[str(init_year)+"-"+str(last_year)].max(10) ].name
    losers  = diff[ diff[str(init_year)+"-"+str(last_year)].min(10) ].name

    return (winners,losers)

def plot_vcs_dynamics(gdf, countries):
    """
    Plots the vegetation carbon stock dynamics for all the available years and
    only the specified countries.
    :param gdf: the dataset.
    :param countries: is a Series with the country names.
    :return: a plot of the vegetation carbon dynamics.
    """

    # Restrict the dataset to the specified countries.
    gdf = gdf[ gdf.names == countries ]

    # Drop the geometry column.
    gdf = gdf.drop(columns=["geometry"])

    # Tidy the dataframe.
    gdf = pd.melt(gdf, id_vars="name", var_name="year", value_name="vcs")

    fig, ax = plt.subplots(1, 1)

    # Create the figure.
    sns.relplot(data=gdf,
                ax=ax,
                x="year", y="vcs",
                hue="name",
                kind="line",
                markers=True
    )


def plot_vcs_map(gdf, year, vcs_range):
    """
    Plots the vegetation carbon stock world maps for the specified year.
    :param gdf: is the dataset.
    :param year: the year to visualize.
    :param vcs_range: is a tuple with the minimum and maximum vegetation carbon
    stock values in the dataset to produce colorbars consistent across every year.
    :return: a global map of the vegetation carbon stocks for the specified year.
    """

    gdf = gdf[[year,"geometry"]]

    fig, ax = plt.subplots(1, 1)

    # Need to figure out how to specify colorbar ranges.
    gdf.plot(column=year,
             ax=ax,
             legend=True,
             legend_kws={'label':"Vegetation Carbon Stock (tonnes)"},
             cmap = 'summer',
    )

    ax.set_axis_off();


def plot_vcs_differences_map(gdf, init_year, last_year):
    """
    Plots the vegetation carbon stock relative differences between two specified
    years.
    :param gdf: is the dataset.
    :param init_year: is the initial year to compute the difference.
    :param last_year: is the last year to compute the difference.
    :return: a world map of the relative difference in carbon stock for every
    country and between the two specified years.
    """

    diff = vcs_differences(gdf, init_year, last_year, last_year - init_year)

    fig, ax = plt.subplots(1, 1)
    diff.plot(column=str(init_year)+"-"+str(last_year),
              ax=ax,
              legend=True,
              legend_kws={'label':"Vegetation Carbon Stock Relative Change"},
              cmap = 'RdBu',
    )
    ax.set_axis_off();


def plot_carbon_stock_distribution(gdf,year):
    """
    Plots the distribution of vegetation carbon stock across countries for a
    specified year.
    :param gdf: is the dataset.
    :param year: is the year of the analysis.
    :return: a figure depicting the distribution of vegetation carbon stocks
    across countries.
    """

    gdf = gdf[[year,"geometry"]]

    fig, ax = plt.subplots(1, 1)

    sns.displot(data=gdf,
                ax=ax,
                x=year,
                kind="kde",
                fill=True,
                cut=0
    )


def plot_difference_vs_average(gdf, init_year, last_year):
    """
    Creates a scatter plot of relative difference in vegetation carbon stock vs.
    the vegetation carbon stock at the first year.
    :param gdf: is the dataset.
    :param init_year: is the initial year to compute the difference and calculate
    the mean.
    :param last_year: is the last year to compute the difference and calculate
    the mean.
    :return: a scatter plot of relative change vs. average vegetation carbon stock.
    """

    diff = vcs_differences(gdf, init_year, last_year, last_year - init_year)
    gdf0 = gdf[[str(init_year),"name"]]

    gdf = pd.merge(diff, gdf0, on = ["name"])

    fig, ax = plt.subplots(1, 1)

    sns.jointplot(data=gdf,
                  ax=ax,
                  x=str(init_year),
                  y=str(init_year)+"-"+str(last_year)
    )



file_list = get_vcs_filenames("./temp_data/")
vcs_df = merge_vcs_all_years(file_list)
countries_gdf = load_countries_polygon_data("./temp_data/2015_gaul_dataset_mod_2015_gaul_dataset_global_countries_1.shp")
gdf = join_vcs_with_country(vcs_df,countries_gdf)
diff_all = vcs_differences(gdf,2001,2005,5)


#
# def plot_vcs_per_year(vcs_files, countries_gdf):
#     """
#     Produces global maps of the vegetation carbon stock for every year.
#     """
#     for file in vcs_files:
#
#         year = extract_year_from_name(file)
#
#         vcs_percountry = join_vcs_with_country(file, countries_gdf)
#
#         fig, ax = plt.subplots(1, 1)
#         vcs_percountry.plot(column='vcs',
#                             ax = ax,
#                             legend=True,
#                             legend_kwds={'label': "Vegetation Carbon Stock (tonnes)"},
#                             missing_kwds={"color": "lightgrey"},
#                             cmap='summer')
#         ax.set_axis_off();
#         plt.savefig("./figures/vcs_"+str(year)+".png" , bbox_inches='tight')
