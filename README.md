# Country-level vegetation carbon stock

This repository hosts a _Python_ script used to process the vegetation carbon stock maps produced with k.LAB in order to obtain country-level data. The ARIES model, based on state-of-the-art IPCC methodology, produces global carbon stock maps at a resolution of 300 meters for each year between 2001 and 2020. Each raster tile contains information on the vegetation carbon stock per hectare at the location. The script takes into account national borders and tile area to aggregate carbon stocks at country level, producing, as a result, a ***dataset on total vegetation carbon stocks per country for the whole world and for the last two decades***.  

## Contents of the repository

- The _Python_ script to calculate total vegetation carbon stocks in each country from the maps produced with k.LAB.
- A _Jupyter_ notebook with the same script including step-by-step comments and serving as interactive documentation for the script.
- The country-level carbon stock dataset produced after executing the script in CSV format. 
- A second _Python_ script producing a figure of the global carbon stock per country, as well as other figures for visualization of summary statistics of the country-level carbon stocks (to be determined).

## Outline of the aggregation process

1) Load the global vegetation carbon stock raster files produced by k.LAB for the 2001-2020 period.
2) Load the vector file containing the information on national borders. 
3) Iterate over carbon stock maps (1 per year) and over countries.
4) For each year and each country: iterate over every raster tile belonging to the country, calculate total carbon stock and sum the result.
5) Progressively store the results in a list and produce a final table that is exported in CSV format.  
