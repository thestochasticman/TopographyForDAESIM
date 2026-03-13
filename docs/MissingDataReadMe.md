# Summary of missing data from phenode sensor suite##

Not all the data collected from the phenode weather station and soil moisture sensors was continuous unfortunately so some periods are missing. Overall the data extensively covers the period between late March to late August 2025. Missingness is summarised at the daily level. 

## Wireless sensor data missingness:

The wireless sensors are the 8 soil moisture monitoring positions deployed across 2 management treatments and 2 topographic positions (ridges and gullies), with 2 overall technical replicates. The 8 positions each have 2 sensors at roughly ~10cm and ~30cm depth, making 16 sensors overall. They measure the soil moisture every 15 minutes but have been summarised to the daily average for the purpose of this analysis, and also averaged between the two depths as this better reflects the model outputs of SILO Soil Moisture Estimates. 

A strange error where two weeks of data is missing across all sensors occured when downloading recent data from the Phenode website so I've written some R code to combine the data I downloaded during my honours with the recently downloaded data to remove the gap. (Reference phenode missingness from line)

Alongside the VWC soil moisture from the sensors, LUX was used and converted to mj/m^2/day. The summary of both is presented below: 

**Overall per sensor missingness:** (Reference phenode missingness.rmd output graphs from line)

| Sensor | Overall SM missing % | Overall LUX missing % | 
| --- | ------ | ------| 
| EOR | 28.656716 | 3.5820896 | 
| EER | 2.3880597 | 2.3880597 |
| EOG | 20.298507 | 2.3880597 |
| EEG | 3.2835821 | 3.5820896 |
| AOR | 0.0000000 | 0 |
| AOR (old) | 15.5844156 | 0 |
| AER | 4.3478261 | 4.3478261 |
| AOG | 0.3623188 | 0.3623188 |
| AEG | 2.8985507 | 2.8985507 |

Note: AOR (old) is a sensor that broke on the 3rd of May, 2025. 


## Weather station data missingness: 

There are two weather stations installed on the study property (Esdale = ANU 3 and Adnamira = ANU 4), they are approximately ~1km distant from one another. ANU 4 was installed first (February 24) and ANU 3 was installed later (Maybe May 14) and both have had outages and sensor failures so I decided to combine them to fill any gaps. 

| Variable | % missing |
| -------  | --------- |
| Temperature | 0.69 | 
| Atmospheric pressure | 17.7 | 
| Relative humidity | 17.7 |
| Vapour pressure | 17.7 | 
| VPD | 17.7 | 
| Wind speed | 0.69 | 
| Rain | 0 | 

