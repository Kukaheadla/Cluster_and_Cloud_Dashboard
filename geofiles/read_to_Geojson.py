import geopandas as gpd
import pandas as pd, json
from shapely.geometry import Point, shape
from shapely.geometry.polygon import Polygon


#Convert the centroid value to a Point object.
def convert_centroid_to_point(tweet):
    ret = []
    tweet_spt = tweet.split(",")
    ret[0] = tweet_spt[0][1:]
    ret[1] = tweet_spt[1][1:-1]
    return ret

#Check if point lines in shapefile or not:
def within_file(point, shapes):
    for shape in shapes:
        if shape != None:
            if shape.contains(point) or shape.touches(point):
                #Point contained
                return True
    return False

#Overall function:
def read_to_GeoJSON(json_filename):
    #First read in the shapefile.
    #This will be used to check if the Point objects are in Australia or not.
    shapefile = gpd.read_file("SA2_2021_AUST_SHP_GDA2020/SA2_2021_AUST_GDA2020.shp")
    
     with open(json_filename, "r") as f:
        for line in f.readlines():
            print("line = ", line[:5])
            if line[:5] == '{"id"':
                print(line)
                if line[-2] == ',':
                    line = line[:-2]
                elif line[-2] != ',' and line[-3] == ']':
                    line = line[:-3]
                tweet = json.loads(line)
                if "geo" in tweet.keys() and tweet["geo"] != {}:
                    #If the coordinates attribute is available we use that and the centroid.
                    if "coordinates" in tweet["geo"].keys():
                        tmp.append(Point(tweet["geo"]["coordinates"]))
                    elif "coordinates" not in tweet["geo"].keys():
                        tmp.append(Point(convert_centroid_to_point(tweet["geo"]["geo_location"]["centroid"])))
                        
        #Now check to see which points are in Australia.
        australia = []
        lat = []
        long = []
        marker = []
        
        for point in geo_points:
            if within_file(point, shapefile.geometry):
                print("In Australia")
                australia.append(point)
                marker.append("#009C54")
        
        #Combine the results to form a GeoDataFrame.
        df2 = {"marker" : marker, "geometry" : australia}
        gdf = gpd.GeoDataFrame(df2)
        
        #Finally read the GeoDataFrame to a file.
        gdf.to_file("output.geojson", driver="GeoJSON")
        return
