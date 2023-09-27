# CODE TO CONVERT TO DATAFRAME
# Parsing files


import pickle
import fitparse
import pandas as pd
import numpy as np
import os

directory = 'C:/Users/lukas/Desktop/DPS_UTUM/batch14_Fazua_ai/Input'
df_merged = pd.DataFrame()

# Iterate over files in directory
for filename in os.listdir(directory):
    if filename.endswith(".fit"):
        # Load the FIT file
        fitfile = fitparse.FitFile('C:/Users/lukas/Desktop/DPS_UTUM/batch14_Fazua_ai/Input/' + filename)
        columns = {'FZ_Assist': [], "FZ_Bat_Power": [], 'FZ_User_Pwr': [], 'FZ_Cadence': [], 'FZ_Rem_Ah': [],
                   'FZ_SOC': [], 'FZ_Speed': [], 'FZ_User_Torque': [], 'distance': [], 'altitude': [],
                   'position_lat': [], 'position_long': []}
        # Iterate over all messages of type "record"
        # (other types include "device_info", "file_creator", "event", etc)
        for record in fitfile.get_messages("record"):
            # Records can contain multiple pieces of data (ex: timestamp, latitude, longitude, etc)
            x = []
            for data in record:
                string = str(data.name)
                x.append(string)

            if set(columns.keys()).issubset(
                    set(x)):  # if gps signal not working and there is no data -> skip the record
                for data in record:
                    string = str(data.name)
                    if string in columns:
                        columns[string].append(data.value)
            else:
                continue

        df = pd.DataFrame(columns)
        # drop irrelevant rows
        df = df[df.FZ_SOC != 0]  # ignore values where SOC=0
        df.drop(index=df.index[0],
                axis=0,
                inplace=True)

        ## Calculate slope for moving average (5 timesteps)
        # Create new Dataframe df2 to calculate moving average
        df2 = df.groupby(np.arange(len(df)) // 20).mean()

        # Create new Dataframe df3 to calculate fixed values like distance and altitude and update df2 with these values
        df3 = df.iloc[::20, :]
        df3.drop(['FZ_Bat_Power', 'FZ_User_Pwr', 'FZ_Cadence', 'FZ_Speed', 'FZ_User_Torque'], axis=1, inplace=True)
        df3.reset_index(inplace=True, drop=True)
        df2.update(df3)

        ##Calculation of slope and total power
        # shift dataframe for calculation of delta distance and altitude
        df4 = df2.shift(-1)

        # columns for calculation
        df2["altitude_2"] = df4["altitude"]
        df2["distance_2"] = df4["distance"]
        df2["delta_dist"] = None
        df2["delta_alt"] = None

        # Calculate delta_alt and delta_dist (height and distance)
        for i in df2.index:
            df2.at[i, 'delta_alt'] = df2.loc[i]['altitude_2'] - df2.loc[i]['altitude']
            df2.at[i, 'delta_dist'] = df2.loc[i]['distance_2'] - df2.loc[i]['distance']
        df_merged = df_merged.append(df2)
        continue
    else:
        continue

df_merged=df_merged[df_merged.delta_dist != 0]

# slope for distance of about 40m (5 seconds) and total power from cyclist and bike
for i in df_merged.index:
    df_merged.at[i, "slope"] = df_merged.loc[i]["delta_alt"] / df_merged.loc[i]["delta_dist"]
    df_merged.at[i, "power_tot"] = df_merged.loc[i]["FZ_Bat_Power"] + df_merged.loc[i]["FZ_User_Pwr"]
df_merged["slope"] = df_merged["slope"].astype(float) #Convert to datatype float

# Only consider slope between -5% and 80%
df_merged = df_merged[(df_merged.slope >= -0.03) & (df_merged.slope <= 0.20)]

# Filtering values
df_merged=df_merged[(df_merged.FZ_Speed >= 5) & (df_merged.FZ_Speed <= 26)] #only consider speed between 3 and 26 km/h
#df_merged=df_merged[(df_merged.FZ_User_Pwr >= 50) & (df_merged.FZ_User_Pwr <= 350)] #Filter all values above 350 Watt
df_merged = df_merged.drop(columns=['FZ_Cadence','FZ_Rem_Ah','FZ_SOC','FZ_User_Torque','distance','altitude', 'altitude_2','position_lat','position_long','distance_2','delta_dist','delta_alt'])


df_merged.to_pickle("df_merged.pkl")
