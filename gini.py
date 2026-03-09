import wbgapi as wb
import pandas as pd
import geopandas as gdp
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

# World Bank Indicators: https://data.worldbank.org/indicator/SI.POV.GINI

indicators = {
    'SI.POV.GINI': 'Gini', # Gini Coefficient
    'NY.GDP.PCAP.PP.CD' : 'PPP' # GDP per capita (current international $)
}

#ISO-3 country codes
countries = ['ARG', 'BLZ', 'BOL', 'BRA', 'CHL', 'COL', 'CRI', 'ECU', 'GUF', 'GUY', 'SLV', 'GTM', 'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'SUR', 'URY', 'VEN']

print("Getting that data...")
df = wb.data.DataFrame(indicators.keys(), countries, time=range(2000, 2022), columns='series').reset_index()
df = df.rename(columns=indicators)

df['time'] = df['time'].str.replace('YR', '').astype(int)

df['ratio'] = df['Gini'] * 100/df['PPP']

south_america = ['ARG', 'BOL', 'BRA', 'CHL', 'COL', 'ECU', 'GUF', 'GUY', 'PRY', 'PER', 'SUR', 'URY', 'VEN']
df['Region'] = np.where(df['economy'].isin(south_america), 'South America', 'Central Am. & Mexico')



print(df)



