import wbgapi as wb
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from adjustText import adjust_text
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.tsa.stattools import adfuller

indicators = {
    'SI.POV.GINI': 'GINI',
    'NY.GDP.PCAP.PP.CD' : 'GDP_PPP',
    'NY.GNP.PCAP.PP.CD' : 'GNI_PPP',
    'BX.KLT.DINV.CD.WD' : 'FDI', # foreign direct investment
    'AG.LND.FRST.ZS' : 'FOREST_AREA', 
    'EN.GHG.ALL.MT.CE.AR5' : 'TOTAL_GHG',
    'EN.GHG.CO2.PC.CE.AR5' : 'CO2_PER_CAP', # tCO2e/capita
    'BN.CAB.XOKA.CD' : 'BOP' # balance of payments
}

countries = ['ARG', 'BLZ', 'BOL', 'BRA', 'CHL', 'COL', 'CRI', 'ECU', 'GUY', 'SLV', 'GTM', 'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'SUR', 'URY', 'VEN']

print("Getting that data...")
df = wb.data.DataFrame(indicators.keys(), countries, time=range(2000, 2022), columns='series').reset_index()
df = df.rename(columns=indicators)

df['time'] = df['time'].str.replace('YR', '').astype(int)


df_clean = df.dropna(subset=['GINI']).sort_values('time').groupby('economy').last().reset_index()

# geopandas shapefile
shapefile_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(shapefile_url)
map_data = world.merge(df_clean, how='inner', left_on='ADM0_A3', right_on='economy')

# viz
fig, ax = plt.subplots(1, 1, figsize=(16, 14))

# base map to show countries with no values (in grey)
world[world['ADM0_A3'].isin(countries)].plot(ax=ax, color='lightgrey', edgecolor='white')

map_data.plot(
    column='GINI',
    ax=ax,
    legend=True,
    cmap='viridis', 
    legend_kwds={'label': "Gini Coefficient", 'shrink': 0.4, 'orientation': 'horizontal', 'pad': 0.02},
    edgecolor='black',
    linewidth=0.5
)

# change mercator projection
map_data['centroid'] = map_data['geometry'].to_crs(epsg=3857).centroid.to_crs(map_data.crs)
map_center_x = map_data['centroid'].x.mean()

# list for text boxes
texts = []

for idx, row in map_data.iterrows():
    label_text = f"{row['NAME']}\nGini: {row['GINI']:.2f}\nYear: {int(row['time'])}"
    
    target_x, target_y = row['centroid'].x, row['centroid'].y
    
    minx, miny, maxx, maxy = row['geometry'].bounds
    
    if target_x < map_center_x:
        initial_x = minx - 4 
    else:
        initial_x = maxx + 4

    t = ax.annotate(
        label_text,
        xy=(target_x, target_y),
        xytext=(initial_x, target_y),     
        fontsize=8,
        ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.9, lw=0.5, edgecolor='black'),
        arrowprops=dict(arrowstyle="-", color="black", linewidth=0.8, alpha=0.7, shrinkA=0, shrinkB=0)
    )
    texts.append(t)

# adjust text to prevent overlapping
adjust_text(
    texts, 
    ax=ax,
    force_text=(0.2, 2.0) 
)

total_bounds = map_data.total_bounds
ax.set_xlim(total_bounds[0] - 15, total_bounds[2] + 15)

ax.set_title('Gini Index in Central and South America', fontsize=18, fontweight='bold', pad=20)
ax.set_axis_off()

plt.tight_layout()
plt.show()


# Uruguay broad survey plots

uruguay_data = df[df['economy'] == 'URY']

uruguay_indicators = ['GINI', 'GDP_PPP', 'GNI_PPP', 'FDI', 'FOREST_AREA', 'TOTAL_GHG', 'CO2_PER_CAP', 'BOP']

for indicator in uruguay_indicators:

    plt.figure()

    plt.plot(uruguay_data['time'], uruguay_data[indicator])

    plt.title(f"Uruguay: {indicator}")
    plt.xlabel("Year")
    plt.ylabel("Value")

    plt.show()

# Uruguay EKC (Environmental Kuznet Curve)

ekc_data = uruguay_data[['time', 'GDP_PPP', 'CO2_PER_CAP']].copy().dropna()

ekc_data['ln_GDP'] = np.log(ekc_data['GDP_PPP'])
ekc_data['ln_GDP2'] = ekc_data['ln_GDP'] ** 2 
ekc_data['ln_CO2'] = np.log(ekc_data['CO2_PER_CAP'])

'''
# Augmented Dickey-Fuller
def run_adf_test(series, variable_name):
    result = adfuller(series, autolag='AIC')
    print(f"--- ADF Test for {variable_name} ---")
    print(f"ADF Statistic: {result[0]:.4f}")
    print(f"p-value: {result[1]:.4f}")
    
    if result[1] <= 0.05:
        print("Stationary (Reject Null Hypothesis)\n")
    else:
        print("Non-Stationary (Fail to Reject Null Hypothesis)\n")

print("Testing Stationarity (Levels)")
run_adf_test(ekc_data['ln_GDP'], "Log GDP")
run_adf_test(ekc_data['ln_CO2'], "Log CO2")
'''

# fit ekc with OLS 
print("Fit EKC Model")
ekc_model = smf.ols(formula='ln_CO2 ~ ln_GDP + ln_GDP2', data=ekc_data).fit()
print(ekc_model.summary())

# coefficients
beta_0 = ekc_model.params['Intercept']
beta_1 = ekc_model.params['ln_GDP']
beta_2 = ekc_model.params['ln_GDP2']

#viz

plt.figure(figsize=(10, 6))

plt.scatter(ekc_data['ln_GDP'], ekc_data['ln_CO2'], 
            alpha=0.7, color='teal', edgecolor='black', s=80, label='Uruguay Data Points')

X_plot = np.linspace(ekc_data['ln_GDP'].min(), ekc_data['ln_GDP'].max(), 100)
Y_plot = beta_0 + (beta_1 * X_plot) + (beta_2 * X_plot**2)
plt.plot(X_plot, Y_plot, color='darkred', linewidth=2.5, label='EKC Regression Line')


plt.xlabel('Log of GDP per Capita (PPP)', fontsize=12)
plt.ylabel('Log of CO2 Emissions per Capita', fontsize=12)
plt.title('Environmental Kuznets Curve: Uruguay', fontsize=16, fontweight='bold')
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()