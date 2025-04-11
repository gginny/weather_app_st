# import libraries

import os
import time
import datetime
import base64
import sys
import path
from pathlib import Path

import streamlit as st
import pandas_gbq
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

from google.oauth2 import service_account
from google import genai
from google.cloud import bigquery
from google.genai.types import FunctionDeclaration, GenerateContentConfig, Part, Tool


# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)


# Set the app header
st.header('Storm Preparation and Opportunity ⚡', divider = True) 
st.markdown("<h6 style='text-align: right;'>Ginny Gao</h6>", unsafe_allow_html=True)

# Add a welcome message 
st.markdown("- When a storm/hurricane is coming, what is the estimated impact, what are the preparations companies can do?") 
st.markdown('- What are the oppotunities it could bring?')


st.subheader('Beryl 2024 Houston - WeatherNext Forecast')



work_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(work_dir)


# Insert gif from local
gif_file = open('Beryl_short.gif', 'rb')
contents = gif_file.read()
data_url = base64.b64encode(contents).decode("utf-8")
gif_file.close()

st.markdown(
    f'<img src="data:image/gif;base64,{data_url}" alt="Beryl gif">',
    unsafe_allow_html=True,
)



# Insert link to Earth Engine
ee_url = "https://code.earthengine.google.com/7e205778d5c52c0962ba6f235e2887d4"
st.markdown("View animation on [Google Earth Engine](%s)." % ee_url)



# Create a date selector widget input
date_selector_input = st.date_input('Enter date:', datetime.date(2024, 7, 7)) 
# Display the select date widget
st.write('Date selected:', date_selector_input)

date_selector = date_selector_input.strftime("%Y-%m-%d %H:%M:%S")

# Houston Temp forecast using WeatherNext model


query = """
SELECT
    t1.init_time as `init_time`,
    DATETIME(t2.time, 'America/Chicago') AS `time_CT`,
    (t2.`2m_temperature` - 273.15) * 9/5 + 32 as `2m_temperature_F`,
    SQRT(POW(t2.`10m_u_component_of_wind`, 2) + POW(t2.`10m_v_component_of_wind`, 2)) AS `wind_speed_m_s`,
    t2.total_precipitation_6hr as `total_precipitation_6hr_m`
  FROM
    `ginny-gcp-demo.weathernext_graph_forecasts.59572747_4_0` AS t1, t1.forecast AS t2
  WHERE ST_INTERSECTS(t1.geography_polygon, ST_GEOGFROMTEXT('POLYGON((-95.2481 29.8767, -95.2810 30.2825, -95.4601 29.7765, -95.2481 29.8767))'))  # Houston    
  AND t1.init_time BETWEEN TIMESTAMP('2024-05-01 00:00:00 UTC') AND TIMESTAMP('2024-07-30 00:00:00 UTC')
  ORDER BY t2.time
"""


df_Hou_T_W_P = pandas_gbq.read_gbq(query, credentials=credentials)
df_Hou_T_W_P_f = df_Hou_T_W_P.loc[df_Hou_T_W_P['init_time'] == date_selector]


# filter df based on date user selection
df_Hou_T_W_P_f = df_Hou_T_W_P_f[['time_CT', '2m_temperature_F', 'wind_speed_m_s', 'total_precipitation_6hr_m']]


# Show Houston Temp in dataframe
st.write("Temperature, Wind, Precipitation in Houston:")
st.dataframe(df_Hou_T_W_P_f)


# Plot Houston Temp, Wind speed, Precipitation

# Set the aesthetic style
sns.set_theme(style="white")

# Plot the data with two y-axes
fig, ax1 = plt.subplots(figsize=(18, 12))

# Wind speed
color = 'tab:blue'
sns.lineplot(x='time_CT', y='wind_speed_m_s', data=df_Hou_T_W_P_f, marker='o', linestyle='-', color=color, ax=ax1)
ax1.set_xlabel('Time', fontsize=20)
ax1.set_ylabel('Wind Speed (m/s)', color=color, fontsize=20)
ax1.tick_params(axis='x', labelsize=16)
ax1.tick_params(axis='y', labelcolor=color, labelsize=16)

# Temperature
ax2 = ax1.twinx()  # Instantiate a second axes that shares the same x-axis
color = 'tab:red'
sns.lineplot(x='time_CT', y='2m_temperature_F', data=df_Hou_T_W_P_f, marker='x', linestyle='--', color=color, ax=ax2)
ax2.set_ylabel('Temp (F)', color=color, fontsize=20)
ax2.tick_params(axis='y', labelcolor=color, labelsize=16)

# Precipitation
ax3 = ax1.twinx()  # Instantiate a third axes that shares the same x-axis
color = 'tab:purple'
sns.lineplot(x='time_CT', y='total_precipitation_6hr_m', data=df_Hou_T_W_P_f, marker='*', linestyle='-.', color=color, ax=ax3)
ax3.set_ylabel('Precipitation (m)', color=color, fontsize=20, labelpad=10)
ax3.tick_params(axis='y', labelcolor=color, length=40, labelsize=16)

# Format the x-axis ticks for better readability
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=2))

plt.xticks(rotation=45, ha='right', fontsize=10)

# Add gridlines
plt.grid(True)  # Add gridlines to the plot

plt.title('Temperature, Wind Speed, Precipitation in Houston', fontsize=36)
fig.tight_layout()
st.pyplot(plt.gcf())

