#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Apr 22 14:52:18 2019

@author: persh

program to visualise use of parking plot by date of photos taken as well as
days where we were absent.
The photos are all in my Google calendar album "Parking voitures"
and the absent dates are extracted from my Google calendar "absent from Tartegnin"

    The class CalDates does most of the operations based on Pandas time series
    and dataframes.

     19-5-2019
"""

import pandas as pd
import calplot
import matplotlib.pyplot as plt
from datetime import date

import glib


class GoogleDates:
    """
    Class which access the Glib class to get dates of photos and absences in the format needed for plotting
    """

    def __init__(self, gl):
        self.gl = gl
        return

    def get_parking_dates(self, name):
        parking_id = self.gl.get_album_id(name)
        date_list = self.gl.photo_dates(parking_id)
        cars_df = pd.DataFrame(date_list, columns=['datetime'])
        return self._add_columns(cars_df)

    def get_absence_dates(self, name):
        calendar_id = self.gl.get_gcal_id(name)
        vac_days = pd.DataFrame()
        events = self.gl.gcal_events2_df(calendar_id, '2015-01-01', date.today().isoformat())
        for index, row in events.iterrows():
            adates = pd.DataFrame(pd.date_range(row['start'], row['finish'], freq='D', name='datetime'))
            adates.drop(adates.tail(2).index, inplace=True)  # range is one too long + we may spot car on arrival
            vac_days = vac_days.append(adates, ignore_index=True)
        return self._add_columns(vac_days)

    def _add_columns(self, tdf):
        tdf['datetime'] = pd.to_datetime(tdf['datetime'], utc=True)
        tdf['year'] = tdf['datetime'].dt.year
        tdf['date'] = tdf['datetime'].dt.date
        tdf.drop_duplicates(subset=['date'], inplace=True)  # in case of multiple photos in single day
        return tdf


class CarParkPlot:
    """
    class to generate barplot and heatmap plots
    """

    def __init__(self):
        return

    def year(self, cars_df):
        plt.figure(figsize=(15, 6))
        p_now = date.today().isoformat()
        yearcount = cars_df.groupby('year')['year'].count().to_frame('count')
        yearcount.plot(kind='bar', title=(f'Parking days per year up to {p_now}'))
        plt.show()
        plt.savefig('plots/years_count.png')
        plt.close()
        return

        # plot calendar heatmap for one year with parking and absence days

    def heatmap(self, car, vac, yr):
        plt.figure(figsize=(15, 6))
        car['const'] = .9
        vac['const'] = .6
        events = pd.concat([vac[['date', 'const']], car[['date', 'const']]], axis=0)
        dates = pd.to_datetime(events['date'].values)  # convert dates to datetime. Values to be used as index
        ev = pd.Series(events['const'].values, index=dates)  # calmap expects a Pd.Series with datetime index
        # calplot.calplot(ev, year=yr)
        calplot.calplot(ev)
        ccount = len(car[car['year'] == yr])
        vcount = len(vac[vac['year'] == yr])
        plt.title(f"Year {yr} \n Parking days observed: {ccount},  (Absent {vcount} days)")
        plt.show()
        file_name = f'plots/calendar_{yr}.png'
        plt.savefig(file_name)
        plt.close()
        return


if __name__ == "__main__":
    """
    Program to illustrate use of Parking as function of time.
    Generates a bar plot with number of observed parking days per year
    as well as heatmap for each year showing the dates of parking photos 
    plus the dates, where we we absent from Tartegning

    The absence data is read from Google calendar "Not in Tartegnin"

    The parking photo dates are read from Google photos album "Parking voitures"
    """

    # constants
    START_YEAR = 2018
    CALENDAR = 'Not in Tartegnin'
    PARKING = 'Parking voitures'

    SCOPE = ['https://www.googleapis.com/auth/drive.readonly',
             'https://www.googleapis.com/auth/photoslibrary.readonly',
             'https://www.googleapis.com/auth/spreadsheets.readonly',
             'https://www.googleapis.com/auth/calendar']

    # Instantiate Glib to Input dataes from Google photos and Google Calendar
    gl = glib.Glib(SCOPE)

    # get objects of google dates and carpark plot classes
    cars = GoogleDates(gl)
    plots = CarParkPlot()

    # Read dates of all photos of parking and plot the distribution per year

    pdates_df = cars.get_parking_dates(PARKING)
    plots.year(pdates_df)

    # Read all absence dates from Google calender and make a heatmap plot per year
    # showing exact days of parking as well as absences from Tartegnin

    this_year = date.today().year
    abdates_df = cars.get_absence_dates(CALENDAR)
    for year in range(START_YEAR, this_year + 1):
        plots.heatmap(pdates_df, abdates_df, year)
    print('end of execution. The plots are in sub folder plots')
    exit(0)
