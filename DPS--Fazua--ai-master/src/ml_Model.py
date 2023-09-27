# -*- coding: utf-8 -*-
# Designed by: Lukas Bock
#-------------
# Created on: 30.11.2021
# ------------
# Version: Python 3.9.7, Spyder 4.0.1
# -------------
# Description: 
# This schript is used to xxx. The method is applied to a data set which contains 
# the xxx.
# ------------
# Input: 
#   Input data (gpx file) -> (xxx)

# %% Import libraries and functions

# Import libraries
import pandas as pd
import fitparse
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (PolynomialFeatures, QuantileTransformer,MinMaxScaler, Normalizer, PowerTransformer, RobustScaler, StandardScaler, quantile_transform)
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import (LinearRegression,Lasso,Ridge, RidgeCV,SGDRegressor,LassoLarsCV, BayesianRidge,MultiTaskElasticNet, TheilSenRegressor, RANSACRegressor, HuberRegressor)
import pickle
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

df_merged = pd.read_pickle("df_merged.pkl")
## Prediction model

X = df_merged[["slope", "FZ_Speed"]]
#X = df_merged["FZ_Speed"]
#X = df_merged["slope"]
y = df_merged["FZ_Bat_Power"] # output variable of interest
X = X.values.reshape(-1,2)
#X = X.values.reshape(-1,1)

#df2.at[i, "power_tot"] = df2.loc[i]["FZ_Bat_Power"] + df2.loc[i]["FZ_User_Pwr"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state = 15) # split data first

pipeline = Pipeline(steps = [          # build entire pipline
    ('transformer', PolynomialFeatures(5)),
    ('scaler',  RobustScaler()),
    ('model',Ridge(alpha=0.01)),
])

pipeline.fit(X_train, y_train) # fit pipeline
y_hat = pipeline.predict(X_test) # predict using pipeline object
print(y_hat)
def rms(y, y_hat):
    return np.sqrt(np.mean((y-y_hat)**2))
print('Root mean squared error: %.2f'%rms(y_test, y_hat))

# save the model to disk
filename = 'finalized_model.sav'
pickle.dump(pipeline, open(filename, 'wb'))

loaded_model = pickle.load(open(filename, 'rb'))
result = loaded_model.score(X_test, y_test)
print("Accuracy2: " + str(result))


## scatter plot predicted power and actual power (test data)
# include more data -> include all files
# signifikanz
# preprocessing
# visualize training and test data degree
# cross validation -> validation data