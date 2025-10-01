import math
import random
from datetime import time, datetime, timedelta

from model.RoutingStep import *
from abc import ABC, abstractmethod

seconds_in_day = 60*60*24


# This class describes an agent (i.e. a model of some car) with specific demands
# to a given map and distinct locations. It is abstract and needs a concrete character
# implementation (e.g. Worker), see AgentType.py
class Agent(ABC):
    # Constructor
    # id: A vehicle ID for the given agent
    # locations: A list of locations the agent is able to visit
    # home: A distinct home location
    def __init__(self, vehicle_id, home):
        self.id = vehicle_id
        self.home = home

        self.current_time = None
        self.start_time = None
        self.current_location = home
        self.trip_ids = []

    # Generate car demand for a given number of days, starting now.
    # Returns an array of RoutingStep objects.
    def generate_demand(self, number_of_days):
        output = []
        self.current_location = self.home
        self.start_time = self.current_time = datetime.strptime('2022-02-28 00:00:00', '%Y-%m-%d %H:%M:%S')
        stop_timedate = self.current_time + timedelta(days=number_of_days)
        while self.current_time < stop_timedate:
            next_day = self.generate_day()
            if next_day is not None:
                output.extend(next_day)
        return output

    # Generate a single demand step.
    # Behavior is implemented by child classes.
    @abstractmethod
    def generate_day(self):
        pass

    # Advance the agent to a location and print the details.
    # destination: destination location object
    # stay_time: time to delay after reaching destination
    # returns RoutingStep object
    def advance_step(self, destination, stay_time):
        self.print_route(self.current_time, self.current_location, destination)
        depart = str(math.floor((self.current_time - self.start_time).total_seconds() /10 ))  # set speed factor to /10 for final simulations
        new_step = RoutingStep(self, depart, self.current_location, destination)
        self.trip_ids.append(new_step.id)
        self.current_location = destination
        self.current_time += stay_time
        return new_step

    # --- UTILITY FUNCITONS ---

    # Print the routing step which is to be written
    def print_route(self, timestamp, start, end):
        print(self.id + ' at ' + timestamp.strftime('%H:%M:%S') + ': ' + start.edge_id + ' -> ' + end.edge_id)

    # Convert hourly float value to python time
    def time_from_float(self, timefloat):
        hours = math.floor(timefloat)
        minutes = int((timefloat - hours) * 60)
        return time(hours, minutes)

    # Convert hourly float value to python timedelta
    def timedelta_from_float(self, timefloat):
        hours = math.floor(timefloat)
        minutes = int((timefloat - hours) * 60)
        return timedelta(hours=hours, minutes=minutes)

    # End day and advance to the next one
    def end_day(self):
        self.current_time += timedelta(days=1)
        self.set_time_hm(0, 0)

    # Set current time to a time in terms of hours and minutes
    def set_time_hm(self, h, m):
        self.set_time_t(time(hour=h, minute=m))

    # Set current time to a python time value
    def set_time_t(self, t):
        self.current_time = datetime.combine(self.current_time, t)
