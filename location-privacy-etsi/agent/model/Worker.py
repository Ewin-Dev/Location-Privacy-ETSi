from datetime import timedelta
from datetime import time
from datetime import datetime
from datetime import date

import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType



class Worker(Agent):
    # Constructor
    # id: A vehicle ID for the given agent
    # locations: A list of locations the agent is able to visit
    # home: A distinct home location
    # chore: chore that is done during the week and on the weekend
    # work: A distinct work location
    def __init__(self, vehicle_id, home, work, chore, weekend_chores):
        super().__init__(vehicle_id, home)
        self.type = AgentType.WORKER
        self.chore = chore
        self.work = work
        self.weekend_chores = weekend_chores

        work_time_float = random.normalvariate(8, 1)
        work_duration_float = random.normalvariate(8, 1)
        self.work_time = self.time_from_float(work_time_float)
        self.work_duration = self.timedelta_from_float(work_duration_float)

        chore_time_float = random.uniform(work_time_float + work_duration_float, 22)
        chore_duration_float = random.uniform(0, 23 - chore_time_float)
        self.chore_time = self.time_from_float(chore_time_float)
        self.chore_duration = self.timedelta_from_float(chore_duration_float)

        self.weekend_chore_times = []
        prev_time = 6
        max_time = 23
        for i in range(len(weekend_chores)):
            chores_remaining = (len(weekend_chores) - i)
            remaining_time = max_time - prev_time - 0.5 * chores_remaining
            prev_time = random.uniform(prev_time, prev_time + remaining_time / chores_remaining)
            prev_time += 0.5
            self.weekend_chore_times.append(self.time_from_float(prev_time))

    # Generate a days worth of actions for the given agent.
    # Returns an array of RoutingStep objects
    def generate_day(self):
        actions = []
        if self.current_time.weekday() < 5:

            # Departure time with a random perturbation
            departure_time = (datetime.combine(date.today(), self.work_time) + timedelta(seconds=random.normalvariate(600,300))).time()

            self.set_time_t(departure_time) #without randomness use self.set_time_t(self.work_time)
            a1 = self.advance_step(self.work, self.work_duration)
            a2 = self.advance_step(self.home, timedelta(0))
            self.set_time_t(self.chore_time)
            a3 = self.advance_step(self.chore, self.chore_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2, a3, a4])
            self.end_day()
        else:
            for i in range(len(self.weekend_chore_times)):
                self.set_time_t(self.weekend_chore_times[i])
                a = self.advance_step(self.weekend_chores[i], timedelta(0))
                actions.append(a)
            self.end_day()
        return actions
