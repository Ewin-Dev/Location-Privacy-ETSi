import numpy as np

# Erster Prototyp einer endlichen FSM mit zeitlich konstanten
# wahrscheinlichkeiten. Generiert für einen Agenten die jeweils
# nächsten Ziele anhand einer Wahrscheinlichkeitsmatrix.
class LocationMachine:
    def __init__(self, agent):
        self.agent = agent

    # Generates a random next location according to a weighted
    # distribution given by the matrix above.
    def next_step(self, current_time, current_location):
        return None