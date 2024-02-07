
"""
This script aims to benchmark the PyPSA-Eur and PyPSA-Earth
grid topology and electrical parameters against published
TSO (Transmission System Operator) data for the
region of 50Hertz in Germany.

Author(s):
Open Energy Transition gGmbH

Usage:
python pypsa-grid-analysis.py
creates a html file where topologies can be compared

Dependencies:
- pypsa
- folium
- pandas
- numpy

References:
https://www.50hertz.com/de/Transparenz/Kennzahlen/Netzdaten/StatischesNetzmodell/
https://github.com/PyPSA/pypsa-eur
https://github.com/pypsa-meets-earth/pypsa-earth

License:
MIT
"""

import pypsa
import folium
from folium.plugins import MarkerCluster
import pandas as pd
import numpy as np

netzmodell = pd.read_csv(
    "data/StatischesNetzmodell_Datentabelle2023.csv",
    header=[0,1]
)

netzmodell = netzmodell[[
    ('Substation_1','Full_name'),
    ('Longitude_Substation_1','Unnamed: 5_level_1'),
    ('Latitude_Substation_1','Unnamed: 6_level_1'),
    ('Substation_2','Full_name'),
    ('Longitude_Substation_2','Unnamed: 9_level_1'),
    ('Latitude_Substation_2','Unnamed: 10_level_1'),
    ('Unnamed: 18_level_0','Fixed'),
    ('Unnamed: 11_level_0','Voltage_level(kV)'),
    ('Electrical Parameters','Resistance_R(Ω)'),
    ('Unnamed: 22_level_0','Reactance_X(Ω)'),
    ('Unnamed: 23_level_0','Susceptance_B(μS)'),
    ('Unnamed: 24_level_0','Length_(km)'),
]]
netzmodell.columns = netzmodell.columns.droplevel(level=0)

netzmodell = netzmodell.rename(
    columns = {
        "Unnamed: 5_level_1": "lon1",
        "Unnamed: 6_level_1": "lat1",
        "Unnamed: 9_level_1": "lon2",
        "Unnamed: 10_level_1": "lat2",
        "Fixed": "MVA",
        "Resistance_R(Ω)": "r",
        "Reactance_X(Ω)": "x",
        "Susceptance_B(μS)": "b",
        "Length_(km)": "length",
        "Voltage_level(kV)": "kV",
    }
)

# from I to MVA
netzmodell.MVA = netzmodell.MVA * netzmodell.kV / 1e3 * np.sqrt(3)

# rename columns
netzmodell.columns = ['Sub1', 'lon1', 'lat1', 'Sub2', 'lon2', 'lat2', 'MVA', 'kV', 'r', 'x', 'b', 'length']

# generate a non-unique line name to capture lines with same routes for grouping
netzmodell['line_name'] = (
    netzmodell[['Sub1', 'Sub2']]
    .apply(lambda row: ' '.join(sorted([row['Sub1'], row['Sub2']])), axis=1)
)

def parallel_resistance(series):
    """
    Formula for equivalent parallel resistance
    """
    return 1 / sum(1 / series)

netzmodell = (
    netzmodell.groupby("line_name")
    .agg({
        "lon1": "mean",
        "lon2": "mean",
        "lat1": "mean",
        "lat2": "mean",
        "MVA": "sum",
        "kV": "mean",
        "r": parallel_resistance,
        "x": parallel_resistance,
        "b": "mean",
        "length": "mean",
        "Sub1": "first",
        "Sub2": "first",
        })
    .reset_index()
)

netzmodell = netzmodell.loc[:, ~netzmodell.columns.duplicated(keep='last')]

# read PyPSA-Eur network
n = pypsa.Network("data/base_eur.nc")
n.links['country'] = n.links.bus0.map(n.buses.country)
n.lines['country'] = n.lines.bus0.map(n.buses.country)
n.calculate_dependent_values()

# read PyPSA-Earth network
m = pypsa.Network("data/base_earth.nc")
m.links['country'] = m.links.bus0.map(m.buses.country)
m.lines['country'] = m.lines.bus0.map(m.buses.country)
m.calculate_dependent_values()

folium_map = folium.Map(location=[n.buses.y[0], n.buses.x[0]], zoom_start=5)

# Add a buses as marker to the map
bus_cluster = MarkerCluster(name="PyPSA-Eur buses").add_to(folium_map)
for index, bus in n.buses.query("country == 'DE'").iterrows():
    if bus.carrier not in ["AC", "DC"]:
        continue

    color_local = "gray"

    marker = folium.Marker(
        name="Substations",
        location=[bus.y, bus.x],
        popup=index,
        icon=folium.Icon(icon="map-marker", color=color_local),
    )
    marker.add_to(bus_cluster)

bus_cluster_earth = MarkerCluster(name="PyPSA-Earth buses").add_to(folium_map)
for index, bus in m.buses.query("country == 'DE'").iterrows():
    if bus.carrier not in ["AC", "DC"]:
        continue

    color_local = "black"

    marker = folium.Marker(
        name="Substations",
        location=[bus.y, bus.x],
        popup=index,
        icon=folium.Icon(icon="map-marker", color=color_local),
    )
    marker.add_to(bus_cluster_earth)

seen = []
bus_cluster_50 = MarkerCluster(name="50Hertz buses").add_to(folium_map)
for index, bus in netzmodell.iterrows():
    color_local = "red"

    if bus.Sub1 not in seen:
        marker = folium.Marker(
            name="Substations 50Hertz",
            location=[bus.lat1, bus.lon1],
            popup=bus.Sub1,
            icon=folium.Icon(icon="map-marker", color=color_local),
        )
        marker.add_to(bus_cluster_50)
        seen.append(bus.Sub1)

    if bus.Sub2 not in seen:
        marker = folium.Marker(
            name="Substations 50Hertz",
            location=[bus.lat2, bus.lon2],
            popup=bus.Sub2,
            icon=folium.Icon(icon="map-marker", color=color_local),
        )
        marker.add_to(bus_cluster_50)
        seen.append(bus.Sub2)

# Add lines as branches to map
line_cluster_base = MarkerCluster(name="PyPSA-Eur lines").add_to(folium_map)
for index, line in n.lines.query("country == 'DE'").iterrows():
    # branch coordinates
    coordinates_from = n.buses.loc[line.bus0, ["y", "x"]].values
    coordinates_to = n.buses.loc[line.bus1, ["y", "x"]].values
    coordinates = [coordinates_from, coordinates_to]

    color = "gray"
    line_cluster = line_cluster_base
    # add to map
    html = f"s_nom: {line.s_nom} <br>length: {line.length} <br>kV: {line.v_nom} <br>r: {line.r}<br>x: {line.x}"
    folium.PolyLine(coordinates, popup=html, color=color).add_to(line_cluster)


line_cluster_earth = MarkerCluster(name="PyPSA-Earth lines").add_to(folium_map)
for index, line in m.lines.query("country == 'DE'").iterrows():
    # branch coordinates
    coordinates_from = m.buses.loc[line.bus0, ["y", "x"]].values
    coordinates_to = m.buses.loc[line.bus1, ["y", "x"]].values
    coordinates = [coordinates_from, coordinates_to]

    color = "black"
    line_cluster = line_cluster_earth
    # add to map
    html = f"s_nom: {line.s_nom} <br>length: {line.length} <br>kV: {line.v_nom} <br>r: {line.r}<br>x: {line.x}"
    folium.PolyLine(coordinates, popup=html, color=color).add_to(line_cluster)


# Add links as branches to map
link_cluster_earth = MarkerCluster(name="PyPSA-Earth links").add_to(folium_map)
for index, line in m.links.query("country == 'DE'").iterrows():
    if line.carrier not in ["AC", "DC"]:
        continue

    # branch coordinates
    coordinates_from = m.buses.loc[line.bus0, ["y", "x"]].values
    coordinates_to = m.buses.loc[line.bus1, ["y", "x"]].values
    coordinates = [coordinates_from, coordinates_to]

    color = "black"
    link_cluster = link_cluster_earth
    # add to map
    html = f"{index}p_nom: {line.p_nom}<br>p_nom_max: {line.p_nom_max}"
    folium.PolyLine(coordinates, popup=html, color=color).add_to(link_cluster)

link_cluster_base = MarkerCluster(name="PyPSA-Eur links").add_to(folium_map)
for index, line in n.links.query("country == 'DE'").iterrows():
    if line.carrier not in ["AC", "DC"]:
        continue

    # branch coordinates
    coordinates_from = n.buses.loc[line.bus0, ["y", "x"]].values
    coordinates_to = n.buses.loc[line.bus1, ["y", "x"]].values
    coordinates = [coordinates_from, coordinates_to]

    color = "gray"
    link_cluster = link_cluster_base
    # add to map
    html = f"{index}p_nom: {line.p_nom}<br>p_nom_max: {line.p_nom_max}"
    folium.PolyLine(coordinates, popup=html, color=color).add_to(link_cluster)


# Add lines as branches to map
line_cluster_50 = MarkerCluster(name="50Hertz lines").add_to(folium_map)
for index, line in netzmodell.iterrows():
    # branch coordinates
    coordinates_from = line.loc[["lat1", "lon1"]].values
    coordinates_to = line.loc[["lat2", "lon2"]].values
    coordinates = [coordinates_from, coordinates_to]

    color = "red"
    line_cluster_2 = line_cluster_50
    # add to map
    html = f"s_nom: {line.MVA} <br>length: {line.length} <br>kV: {line.kV} <br>r: {line.r},<br>x: {line.x}"
    folium.PolyLine(coordinates, popup=html, color=color).add_to(line_cluster_2)


folium.LayerControl().add_to(folium_map)
folium_map.save("pypsa-grid-analysis.html")