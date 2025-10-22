from datetime import timedelta
from datetime import time
from datetime import datetime
from datetime import date

import random

from model.Agent import Agent
from model.AgentType import AgentType

import numpy as np

class PartTimeWorker(Agent):
    # Constructor
    # id: A vehicle ID for the given agent
    # locations: A list of locations the agent is able to visit
    # home: A distinct home location
    # chore: chore that is done during the week and on the weekend
    # work: A distinct work location
    def __init__(self, vehicle_id, home, work, chores):
        super().__init__(vehicle_id, home)
        self.type = AgentType.PART_TIME
        self.chores = chores
        self.work = work

        self.work_time = self.time_from_float(random.normalvariate(10, 2))
        self.work_duration = self.timedelta_from_float(random.normalvariate(8, 1))

        # Parttime worker works for rather 1, 2, or 3 random days
        self.work_days = np.random.choice(range(5), np.random.choice([1,2,3,4]), replace=False)

        self.chore_days = np.setdiff1d(range(7), self.work_days)

        # Distribute chores randomly around the day
        self.chore_times = []
        prev_time = 6
        max_time = 23
        for i in range(len(chores)):
            chores_remaining = (len(chores) - i)

            # Plan to have at least 30min between all chores
            remaining_time = max_time - prev_time - 0.5 * chores_remaining
            prev_time = random.uniform(prev_time, prev_time + remaining_time/chores_remaining)
            prev_time += 0.5
            self.chore_times.append(self.time_from_float(prev_time))

    # Generate a days worth of actions for the given agent.
    # Returns an array of RoutingStep objects
    def generate_day(self):
        actions = []
        if self.current_time.weekday() in self.work_days:
            departure_time = (datetime.combine(date.today(), self.work_time) + timedelta(seconds=random.normalvariate(600,300))).time()
            self.set_time_t(departure_time)
            a1 = self.advance_step(self.work, self.work_duration)
            a2 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2])
            self.end_day()
        # inactive because ptworker do not drive home after chores
        # elif self.current_time.weekday() in self.chore_days:
        #    for i in range(len(self.chore_times)):
        #        self.set_time_t(self.chore_times[i])
        #        a = self.advance_step(self.chores[i], timedelta(0))
        #        actions.append(a)
        #    self.end_day()
        else:
            self.end_day()
        return actions
