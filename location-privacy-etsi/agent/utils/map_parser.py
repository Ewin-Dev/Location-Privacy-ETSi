from lxml import etree


# This script parses a map file and returns a list of all edges as well
# as a dictionary, which maps districts to their sets of edges.
# filename: Name of a net file
# districts: An array of *convex* polygons, each
# one marking a district on the map
from utils import geometry


def parse_map_edges(filename, districts):
    locations = []
    tree = etree.parse(filename)
    root = tree.getroot()

    junctions = dict()
    for j in root.findall('junction'):
        jid = j.get('id')
        x = j.get('x')
        y = j.get('y')
        junctions[jid] = [float(x), float(y)]

    for e in root.findall('edge'):
        edge_id = e.get('id')
        if e.get('function') != 'internal' and edge_id is not None:
            e_from = e.get('from')
            edge_start = junctions[e_from]
            if edge_start is None:
                continue
            for d in districts:
                if geometry.point_in_convex_polygon(d.polygon, edge_start):
                    d.edges.append(edge_id)
            locations.append(edge_id)
    return locations
