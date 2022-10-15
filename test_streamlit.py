import pandas as pd
import streamlit as st
import geocoder
from time import sleep
import pickle
import pydeck as pdk
import numpy as np
from math import ceil, floor
import altair as alt






def get_coords(loc):
    max_attempts = 5
    # initialize to None
    lat_lng_coords = None
    
    # loop until we get the coordinates or hit max attempts
    i = 0
    while (lat_lng_coords is None):
        g = geocoder.arcgis('{}, Portugal'.format(loc))
        lat_lng_coords = g.latlng
        i += 1
        if i > max_attempts:
            print('too many attempts on trying to obtain coordinates. quiting')
            break
        sleep(0.2)  # a small pause between requests, trying not to be kicked out.

    # print('coordinates for {} required {} call(s) to ArcGIS provider.'.format(pc, i))
    
    latitude = lat_lng_coords[0]
    longitude = lat_lng_coords[1]
    
    return latitude, longitude






# OBTAIN AND PREPARE DATA
# check if file uploaded
data_file = st.sidebar.file_uploader('upload data file', type=['txt', 'csv'], encoding='utf-8')
if data_file == None:
    data_file = 'https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data_concelhos.csv'
df = pd.read_csv(data_file)
df = df.fillna(0)

# dealing with the date column
df['data']= pd.to_datetime(df.data, format='%d-%m-%Y')
df['data']= df['data'].dt.strftime('%Y-%m-%d')   # we need this to ensure the graph displays dates, instead of week days, and month day
df = df.rename(columns={'data':'index'}).set_index('index')




# PAGE TITLE
#st.markdown('COVID-19 EDA')
st.markdown('# COVID-19 PT **{} ~ {}**'.format(df.iloc[0].name, df.iloc[df.shape[0]-1].name))
st.markdown('by Hugo Bertini (data kindly and very hard workingly provided by [Data Science for Social Good Portugal](https://www.dssg.pt/))')





# INTERACTIVE DATA FILTERING
# select districts
district_show = st.sidebar.multiselect("districts", options=list(df.columns), default=['BRAGA', 'PORTO', 'COIMBRA', 'LISBOA', 'SINTRA', 'BEJA', 'FARO'])

# date limits
min_date = 0
max_date = df.shape[0]
n_days = 7

# central date
central_date = st.sidebar.slider('day number', min_value=min_date, max_value=max_date, value=max_date)

# number of days to display
n_days = st.sidebar.slider('number of days to view', min_value=2, max_value=int(ceil(max_date/2)), value=7)

# calculating dataframe ranges based on the dates
date_from = central_date - int(ceil(n_days/2))
date_to   = central_date + int(floor(n_days/2))
if date_from <= min_date:
    date_to = date_to + (min_date - date_from)
    date_from = min_date
if date_to >= max_date:
    date_from = date_from - (date_to - max_date)
    date_to   = max_date

# filtering the data
df_show = df[district_show].iloc[date_from:date_to]



# USER CUSTOMIZATION
show_graph    = st.sidebar.checkbox('Show graph',    value=True)
show_map      = st.sidebar.checkbox('Show map',      value=False)
show_raw_data = st.sidebar.checkbox('Show raw data', value=True)

#coords_df = df[district_show].iloc[date_from:date_to].copy()
coords_df = df.copy()
coords_df = coords_df.transpose()





# GETTING THE LOCATION OF DISTRICTS
try:
    coords_df = pickle.load( open( "portugal-district-coords.pk", "rb" ) )
    if (not len(coords_df) > 0):
        raise Exception("No coordinates data found on file, so please wait while I request the information from the provider...")
except:
    coords = coords_df.apply(lambda row: get_coords(row.name), axis=1)
    coords_df[['latitude', 'longitude']] = pd.DataFrame(list(coords), columns=['latitude', 'longitude'], index=coords_df.index)
    pickle.dump(coords_df, open( "portugal-district-coords.pk", "wb" ) )
# coords from Portugal
pt_coords = get_coords('')









# DISPLAY GRAPH
if show_graph:
    st.line_chart(df_show)
    #alt.Chart(df_show).mark_line().encode(
    #    x = 'data',
    #    y = 'total',
    #)





d = df[district_show].iloc[date_from:date_to]


if show_map:
    # DISPLAY MAP FOR CENTRAL DATE
    st.pydeck_chart(pdk.Deck(
     map_style='mapbox://styles/mapbox/light-v9',
     initial_view_state=pdk.ViewState(
         latitude=40.69290,
         longitude=-8.47946,
         zoom=6,
         pitch=50,
     ),
     layers=[
         pdk.Layer(
            'HexagonLayer',
            #data=coords_df[['longitude', 'latitude']].loc[district_show],
            data=coords_df,
            get_position='[longitude, latitude]',
            radius=10000,
            elevation_scale=50,
            elevation_range=[0, 1000],
            pickable=True,
            extruded=True,
            auto_highlight=True,
            elevation_aggregation = "'SUM'",
         ),
         pdk.Layer(
             'ScatterplotLayer',
             data=coords_df,
             get_position='[longitude, latitude]',
             get_color='[200, 30, 0, 160]',
             get_radius=2000,
         ),
     ],
    ))
    


    # 2D map
    #st.map(coords_df.iloc[:central_date])
    # 3D map
    #st.pydeck_chart(pdk.Deck(
    #    map_style='mapbox://styles/mapbox/light-v9',
    #    initial_view_state=pdk.ViewState(
    #        latitude=pt_coords[0],
    #        longitude=pt_coords[1],
    #        zoom=6,
    #        pitch=40,
    #    ),
    #    layers=[
    #        pdk.Layer(
    #             'HexagonLayer',
    #             data=df_show,
    #             get_position='[latitude, longitude]',
    #             radius=200,
    #             elevation_scale=40,
    #             elevation_range=[0, 1000],
    #             pickable=True,
    #             extruded=True,
    #         ),
    #        pdk.Layer(
    #            'ScatterplotLayer',
    #            data=coords_df,
    #            get_position='[latitude, longitude]',
    #            get_color='[200, 30, 0, 160]',
    #            get_radius=200,
    #        ),
    #    ],
    #))


# DISPLAY RAW DATA
if show_raw_data:
    #st.subheader('raw data:')
    st.dataframe(df_show)
