import wbgapi as wb
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from adjustText import adjust_text

indicators = {
    'SI.POV.GINI': 'Gini',
    'NY.GDP.PCAP.PP.CD' : 'GDP_PPP',
    'NY.GNP.PCAP.PP.CD' : 'GNI_PPP'
}

countries = ['ARG', 'BLZ', 'BOL', 'BRA', 'CHL', 'COL', 'CRI', 'ECU', 'GUY', 'SLV', 'GTM', 'HND', 'MEX', 'NIC', 'PAN', 'PRY', 'PER', 'SUR', 'URY', 'VEN']

print("Getting that data...")
df = wb.data.DataFrame(indicators.keys(), countries, time=range(2000, 2022), columns='series').reset_index()
df = df.rename(columns=indicators)

df['time'] = df['time'].str.replace('YR', '').astype(int)


df_clean = df.dropna(subset=['Gini']).sort_values('time').groupby('economy').last().reset_index()

# maybe plot this later (Sen's formula) for inequality-adjusted income
df_clean['W'] = df_clean['GDP_PPP'] * (1 - (df_clean['Gini'] / 100))

# geopandas shapefile
print("Getting the shapefile...")
shapefile_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(shapefile_url)
map_data = world.merge(df_clean, how='inner', left_on='ADM0_A3', right_on='economy')

# viz
fig, ax = plt.subplots(1, 1, figsize=(16, 14))

# base map to show countries with no values (in grey)
world[world['ADM0_A3'].isin(countries)].plot(ax=ax, color='lightgrey', edgecolor='white')

map_data.plot(
    column='Gini',
    ax=ax,
    legend=True,
    cmap='viridis', 
    legend_kwds={'label': "Gini Coefficient", 'shrink': 0.4, 'orientation': 'horizontal', 'pad': 0.02},
    edgecolor='black',
    linewidth=0.5
)


# centroid targets
map_data['centroid'] = map_data['geometry'].centroid
map_center_x = map_data['centroid'].x.mean()

# list for text boxes
texts = []

for idx, row in map_data.iterrows():
    label_text = f"{row['NAME']}\nGini: {row['Gini']:.2f}\nYear: {int(row['time'])}"
    
    # Target the exact middle
    target_x, target_y = row['centroid'].x, row['centroid'].y
    
    # Determine absolute borders for margin placement
    minx, miny, maxx, maxy = row['geometry'].bounds
    
    if target_x < map_center_x:
        # Pacific margin
        initial_x = minx - 4 
    else:
        # Atlantic margin
        initial_x = maxx + 4

    # Force Matplotlib to create the text AND the line (arrowprops) immediately
    t = ax.annotate(
        label_text,
        xy=(target_x, target_y),          # The anchor in the middle of the country
        xytext=(initial_x, target_y),     # The starting position in the margin
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
    force_text=(0.2, 2.0) # Encourage vertical repelling to clear stacked boxes
)


total_bounds = map_data.total_bounds
ax.set_xlim(total_bounds[0] - 15, total_bounds[2] + 15)

ax.set_title('Gini Index in Central and South America', fontsize=18, fontweight='bold', pad=20)
ax.set_axis_off()

plt.tight_layout()
plt.show()