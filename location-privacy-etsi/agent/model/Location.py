# This class describes some location an agent is able to visit.
class Location:
    # edgeId: ID of the edge the location is seated at
    # timeGenerator: A function that generates a random
    # duration of an agent's average stay
    def __init__(self, edge_id):
        self.edge_id = edge_id

    # return edge ID as string
    def to_string(self):
        return self.edge_id
