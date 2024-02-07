
# PyPSA Grid Analysis

PyPSA Grid Analysis compares the current (v0.9.0) PyPSA-Eur transmission grid database as well as the current (v0.3.0) PyPSA-Earth transmission grid database for a selected region of 50 Hertz in Germany.
This region was chosen because there exists openly available 50Hertz data for the transmission grid.

PyPSA-Eur uses the Entso-E data as base network.
PyPSA-Earth uses Open Street Map sattelite data.
50 Hertz data is taken from https://www.50hertz.com/de/Transparenz/Kennzahlen/Netzdaten/StatischesNetzmodell/

The analysis outlines:
- Grid topology
- Resistances of the lines (Ω)
- Susceptances of the lines (μS)
- Lengths of the lines (km)
- Voltage levels (kV)

# How to Use
Download the .html file, double-click & analyse line by line
or clone the repository and execute it by running
python pypsa-grid-analysis.py

The following python dependencies are required:
- pypsa
- folium
- pandas
- numpy

# LICENSE
All code is published under the MIT License.
`data/base_eur_50Hertz.nc` and `data/base_earth_50Hertz.nc` are published under the CC-BY-4.0 License.
`data/StatischesNetzmodell_Datentabelle2023.csv` has no designated license, and was downloaded [here](https://www.50hertz.com/de/Transparenz/Kennzahlen/Netzdaten/StatischesNetzmodell/).
