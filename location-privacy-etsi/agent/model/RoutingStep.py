import uuid


# This class describes a single travel of an agent between places at a given time.
# It also implements conversion of these steps into XML trip tags.
class RoutingStep:
    # Constructor
    # agent: agent taking part in trip
    # depart: time of departure (in seconds)
    # start: starting location
    # end: goal location
    def __init__(self, agent, depart, start, end):
        self.agent = agent
        self.depart = depart
        self.start = start
        self.end = end
        self.id = str(uuid.uuid4())