# %% Import libraries
import pickle
import numpy as np
from pyproj import Geod
from shapely.geometry import LineString
import json
import pandas as pd
from gpx_converter import Converter
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import base64
app = Flask(__name__)
CORS(app, supports_credentials=True)


## Helperfunctions
def transform_gpx(path):
    df = Converter(input_file=path).gpx_to_dataframe()
    df1 = df.shift(-1)
    df[["latitude_2", "longitude_2", 'altitude_2', 'time_2']] = df1[["latitude", "longitude", 'altitude', 'time']]
    df['diff'] = df['time_2'] - df['time']
    df['duration'] = df['diff'].dt.total_seconds()
    df["dist"] = None
    df1 = df.shift(-1)
    df[["latitude_2", "longitude_2", 'altitude_2', 'time_2']] = df1[["latitude", "longitude", 'altitude', 'time']]
    df.drop(df.tail(1).index, inplace=True)
    df['time_delta'] = df['time_2'] - df['time']
    df['duration'] = df['time_delta'].dt.total_seconds()
    df["dist"] = None
    for i in df.index:
        df.at[i, 'dist'] = (
        (df.loc[i]['latitude'], df.loc[i]['longitude']), (df.loc[i]["latitude_2"], df.loc[i]["longitude_2"]))
        df.at[i, 'altitude_delta'] = df.loc[i]['altitude_2'] - df.loc[i]['altitude']
    geod = Geod(ellps="WGS84")
    df["distance"] = df["dist"].map(lambda x: geod.geometry_length(LineString(x)))

    for i in df.index:
        df.at[i, 'speed'] = (df.loc[i]['distance'] / df.loc[i]['duration']) * 3.6
        df.at[i, 'slope'] = df.loc[i]['altitude_delta'] / df.loc[i]['distance']
    df = df.drop(columns=['dist', 'time_delta', 'time_2', 'altitude_2','longitude_2','latitude_2'])
    df.drop(df.tail(1).index, inplace=True)  # drop last n rows
    df = df[(df.slope >= -0.1) & (df.slope <= 0.8)]
    df = df[(df.speed >= 3) & (df.slope <= 26)]
    print(df)
    return df

def predict(df1):
    model = pickle.load(open('finalized_model.sav', 'rb'))
    X = df1[["slope", "speed"]].to_numpy()
    X = X.reshape(-1, 2)
    y_hat = model.predict(X)
    time = df1["duration"].to_numpy()
    E_loss = np.matmul(y_hat, time) / 3600 # Energy needed during the trip
    print(E_loss)
    E_Bike = 200 # Energy capacity battery E-Bike in Wh -> actually 252Wh but 80% mechanical efficiency
    SOC = ((E_Bike - E_loss) / E_Bike) - 0.2
    print(SOC)
    # Sicherheitsfaktor einführen! -> 10% SOC reduzieren.
    return SOC


# create the Flask app

UPLOAD_FOLDER = 'gpx_file'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
@cross_origin(allow_headers=['Content-Type'])
def index():
    if request.method == "POST":
        #print(request.files['file'])
        #file = request.files['file']
        file = request.get_data()
        #if file is None or file.filename == "":
         #   return jsonify({"error": "no file"})
        try:
            #f = io.StringIO(file)
            gpxString = base64.b64decode(file)
            filename = "temp.gpx"
            #print(filename)
            f = open(filename, 'wb')
            f.write(gpxString)
            f.close()
            #file.save(filename)
            df1 = transform_gpx(filename)
            prediction = predict(df1)
            data = {"prediction": float(prediction)}
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)})

    return "OK"


if __name__ == "__main__":
    app.run(debug=True)
