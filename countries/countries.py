#!/usr/bin/env python
# -*- coding: utf-8 -*-

from osgeo import ogr

class Point(object):
    """ Wrapper for ogr point """
    def __init__(self, lat, lng):
        """ Coordinates are in degrees """
        self.point = ogr.Geometry(ogr.wkbPoint)
        self.point.AddPoint(lng, lat)

    def getOgr(self):
        return self.point
    ogr = property(getOgr)

class Country(object):
    """ Wrapper for ogr country shape. Not meant to be instantiated directly. """
    def __init__(self, shape):
        self.shape = shape

    def getIso(self):
        return self.shape.GetField('ISO2')
    iso = property(getIso)

    def __str__(self):
        return self.shape.GetField('NAME')

    name = property(__str__)

    def contains(self, point):
        return self.shape.geometry().Contains(point.ogr)

class CountryChecker(object):
    """ Loads a country shape file, checks coordinates for country location. """

    def __init__(self, country_file):
        driver = ogr.GetDriverByName('ESRI Shapefile')
        self.countryFile = driver.Open(country_file)
        self.layer = self.countryFile.GetLayer()
        self.countryGuess = None
        self.ogrPoint = ogr.Geometry(ogr.wkbPoint)

    def getCountry(self, lat, lon):
        """
        Checks given gps-incoming coordinates for country.
        Output is either country shape index or None
        """


        self.ogrPoint.AddPoint(lon, lat)  # lon,lat instead of lat,lon
        if self.countryGuess:
            if self.countryGuess.shape.geometry().Contains(self.ogrPoint):
                return self.countryGuess

        for i in range(self.layer.GetFeatureCount()):
            country = self.layer.GetFeature(i)
            if country.geometry().Contains(self.ogrPoint):
                self.countryGuess = Country(country)
                return self.countryGuess

        # nothing found
        return self.countryGuess
