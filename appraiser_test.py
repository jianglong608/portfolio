
# coding: utf-8

# In[1]:

# get_ipython().magic('matplotlib inline')
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import requests
# from IPython.display import display
from geopy.distance import vincenty
import subprocess, os


# In[5]:

import googlemaps
import datetime 
gmaps = googlemaps.Client(key='AIzaSyA13aDAlqyJL4D4tC-qmljWFeQKuPAgeKs')


# In[2]:

# get HUD data for development
# df = pd.read_excel("https://www.huduser.gov/portal/datasets/pis/public_housing_physical_inspection_scores.xlsx",
df = pd.read_excel("/Users/jianglongli/Downloads/public_housing_physical_inspection_scores.xlsx",                   
                  converters={'INSPECTION_ID': str,
                             'DEVLOPMENT_ID': str,
                             'CBSA_CODE': str,
                             'COUNTY_CODE': str,
                             'STATE_CODE': str,
                             'ZIP': str})

df.rename(columns={'LATITUDE': 'lat', 'LONGITUDE': 'lng'}, inplace=True)


# In[3]:

# pick two states for test
locAZ = df.loc[df.STATE_NAME == 'AZ', ['lat', 'lng']]
locCA = df.loc[df.STATE_NAME == 'CA', ['lat', 'lng']]
# locAZ.shape, locCA.shape


# In[4]:

# generating samples from CA
np.random.seed = 0
travels = [locCA.sample(5, replace=False, random_state=i) for i in range(30)]

# rename index
places = list('ABCDE')
for i in range(len(travels)):
    travels[i].index = places


# In[62]:

for i in range(3):
    # pick a trip
    trip = travels[2] 

    # create input file for Concorde TSP solver
    pid = 0
    output = ''
    for place in places:
        output += '%d %f %f\n' % (pid, trip.loc[place, 'lat'], trip.loc[place, 'lng'])
        pid += 1

    header = """NAME : TSP
    COMMENT : Traveling Salesman Problem
    TYPE : TSP
    DIMENSION : %d
    EDGE_WEIGHT_TYPE : GEO
    NODE_COORD_SECTION
    """ % pid

    with open('aprsr.tsp', 'w') as output_file:
        output_file.write(header)
        output_file.write(output)

    # !concorde aprsr.tsp
    #     output = subprocess.check_output(['concorde', 'aprsr.tsp'])

    os.system('concorde aprsr.tsp')

    # after running the Concorde executable, parse the output file
    solution = []
    f = open('aprsr.sol', 'r')
    for line in f.readlines():
        tokens = line.split()
        solution += [int(c) for c in tokens]
    f.close()

    assert solution[0] == len(places)
    solution = solution[1:]  # first number is just the dimension
    assert len(solution) == len(places)

    # fetching optimal path
    optimal_path = []
    for solution_id in solution:
        optimal_path.append(places[solution_id])

    optimal_path = pd.Series(optimal_path)

    # compute total distance in optimal path
    total = 0
    for i in range(len(optimal_path)):
        if i != len(optimal_path)-1:
            total += vincenty(trip.loc[optimal_path[i]], trip.loc[optimal_path[i+1]]).miles
        else:
            total += vincenty(trip.loc[optimal_path[i]], trip.loc[optimal_path[0]]).miles

    # using googlemap API
    import googlemaps
    import datetime 
    gmaps = googlemaps.Client(key='AIzaSyA13aDAlqyJL4D4tC-qmljWFeQKuPAgeKs')

    direction = gmaps.directions(trip.iloc[0], trip.iloc[0], mode="driving",
                                 waypoints=[trip.iloc[i] for i in range(1, len(trip))], optimize_waypoints=True)
    leg = direction[0]['legs']
    dur_trips = [leg[i]['duration']['value'] for i in range(len(leg))]
    mil_trips = [leg[i]['distance']['value'] for i in range(len(leg))]
    duration = round(sum(dur_trips)/(60*60), 2)
    miles = round(sum(mil_trips)/1609.34, 2)

    print(total, miles)


# In[ ]:



