# countrycarbonaggregation

- In this code we calculate the total carbon pero country with a csv as an output with the values classified in different years
- summary of the process:
  - get both rasters and vector data
  - adapt a table for the output
  - iterate over the rasters and iterate over the vector data
  - do the masking and sum the values of the output raster (array)
  - collect the results into a list
  - append the results to the adapted final table