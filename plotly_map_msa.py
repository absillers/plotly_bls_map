import pandas as pd
import numpy as np
import os
import geopandas as gpd
import json
import plotly.express as px
import plotly.graph_objects as go
import re
import plotly.offline as pyo
import warnings

#download MSA geoIDs
import requests
url = 'https://www2.census.gov/programs-surveys/cbp/technical-documentation/reference/metro-area-geography-reference/msa_county_reference22.txt'

response = requests.get(url)
msa_txt = response.text
msa_csv = msa_txt.split('","')
msa_clean = [x for y in msa_csv for x in y.split('"\n"')]

GEOID = []
MSA_NAME = []
STATE_FIPS = []
CITY_FIPS = []
COUNTY = []

for i in range(len(msa_clean)):
    txt = msa_clean[i]

    if i % 5 == 0:
        GEOID.append(txt)
    if i % 5 == 1:
        MSA_NAME.append(txt)
    if i % 5 == 2:
        STATE_FIPS.append(txt)
    if i % 5 == 3:
        CITY_FIPS.append(txt)
    if i % 5 == 4:
        COUNTY.append(txt)

MSA_geoids = pd.DataFrame({'GEOID':GEOID, 'MSA_NAME':MSA_NAME})
MSA_geoids = MSA_geoids.iloc[1:]
MSA_geoids = MSA_geoids.drop_duplicates()

#drop "Micro area" and "macro area"

MSA_geoids['MSA_NAME'] = MSA_geoids['MSA_NAME'].apply(lambda x: x.replace(" Micro Area", ''))
MSA_geoids['MSA_NAME'] = MSA_geoids['MSA_NAME'].apply(lambda x: x.replace(" Metro Area", ''))

MSA_geoids = MSA_geoids.rename(columns = {'MSA_NAME': 'Area'})

msa = gpd.read_file(r'C:\Users\annas\OneDrive\Github\plotly_bls_map\cbsa_shape\cb_2025_us_cbsa_500k.shp')
msa = msa.to_crs(epsg=4326)
msa.to_file(r'C:\Users\annas\OneDrive\Github\plotly_bls_map\cbsa_shape\cb_2025_us_cbsa_500k.geojson', driver='GeoJSON', index=False)

msa = (r'C:\Users\annas\OneDrive\Github\plotly_bls_map\cbsa_shape\cb_2025_us_cbsa_500k.geojson')

with open(msa) as f:
    msa = json.load(f)

states = pd.read_excel('state_abr.xlsx')
dir_path = r'C:\Users\annas\OneDrive\Github\plotly_bls_map\state_employment_data'
files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

warnings.filterwarnings("ignore", category=UserWarning)

#make a dictionary of each state name and DF
df_name = states['ABR']

datasets = {}
for i in range(0, len(df_name)):
    a = df_name[i]

    if f'{df_name[i]}.xlsx' in os.listdir(dir_path):
        datasets[a] = pd.read_excel(f'{dir_path}/{a}.xlsx', skiprows = 2)
    else:
        continue

def add_county_column(df):
    df['MSA'] = df['Area'].apply(lambda x: str(x)[:-4])

def industry_percentage_by_msa(df):
    df['Percent'] = (df['Employment (1)'] / df.groupby('MSA')['Employment (1)'].transform('sum') * 100)

def replace_non_reported(df):
    df['Employment (1)'] = df['Employment (1)'].replace('(8) -', None)

def add_state_name(df, state_name):
    df['State'] = str(state_name)

for k, v in datasets.items():
    replace_non_reported(v)
    add_county_column(v)
    industry_percentage_by_msa(v)
    add_state_name(v, k)

plotly_msa_employment = pd.concat(datasets.values(), ignore_index=True)
plotly_msa_employment = plotly_msa_employment.dropna(subset = ['Industry'])
plotly_msa_employment = pd.merge(plotly_msa_employment, MSA_geoids, on="Area", how="left")

plotly_msa_employment_construction = plotly_msa_employment[plotly_msa_employment['Occupation'] == 'Construction and Extraction Occupations (47-0000)']
plotly_msa_employment_construction = plotly_msa_employment_construction[plotly_msa_employment_construction['GEOID'] != "NaN"]

plotly_msa_employment_construction = plotly_msa_employment_construction.iloc[1:100,]
plotly_msa_employment_construction = plotly_msa_employment_construction.drop(columns = 'Industry')
plotly_msa_employment_construction = plotly_msa_employment_construction.drop(columns = 'Area')



fig = px.choropleth_map(plotly_msa_employment_construction, 
                            geojson=msa, 
                            locations='GEOID',
                            featureidkey='properties.GEOID',
                            color='Percent',
                           color_continuous_scale="sunsetdark",
                           range_color=(0, 12),
                           map_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.7,
                          )


fig.write_html('plot.html', include_plotlyjs='cdn')        