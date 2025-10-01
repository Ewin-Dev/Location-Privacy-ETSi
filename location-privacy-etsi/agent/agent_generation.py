# coding: utf-8
from model.Worker import Worker
from model.PartTimeWorker import PartTimeWorker
from model.NightWorker import NightWorker
from utils import map_parser
from model.Agent import *
from model.District import *
from model.Location import *
from lxml import etree
import csv
import argparse
import sys
import time
import numpy as np
from datetime import datetime


# Parse map and create locations from edges
def create_test_locations(map_path):
    locations = []
    edges = map_parser.parse_map_edges(map_path, districts)
    for e in edges:
        loc = Location(e)
        locations.append(loc)
        for d in districts:
            if e in d.edges:
                d.locations.append(loc)
    return locations


# create and test agents
def create_test_agents(number, locations):
    test_agents = []
    number_of_parttime_workers = int(number*parttime_percentage)
    nummber_of_nighttime_workers = int(number*nighttime_percentage)
    for i in range(number):
        if i < number_of_parttime_workers:
            test_agents.append(
                PartTimeWorker('pt_worker' + str(i),
                               random.choice(home_district.locations),
                               random.choice(work_district.locations),
                               np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False)))
        elif i < number_of_parttime_workers + nummber_of_nighttime_workers:
            test_agents.append(
                NightWorker('n_worker' + str(i),
                       random.choice(home_district.locations),
                       random.choice(work_district.locations),
                       random.choice(locations),
                       np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False)))
        else:
            test_agents.append(
                Worker('worker' + str(i),
                       random.choice(home_district.locations),
                       random.choice(work_district.locations),
                       random.choice(locations),
                       np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False)))
    return test_agents


# Generate sorted demand XML tags
def generate_demand(agents, duration):
    demand = []
    for a in agents:
        demand += a.generate_demand(duration)
    demand.sort(key=lambda x: int(x.depart), reverse=False)
    return demand


# Generate entire demand and file.
def generate_demand_file(filename, agents, duration):
    root = etree.Element('routes')
    for a in agents:
        root.append(etree.Element('vType', id=a.id, accel='1.0', decel='5.0',
                         length='5.0', maxSpeed='50.0', sigma='0.0'))
    demand = generate_demand(agents, duration)
    for d in demand:
        # Cannot use the typical constructor etree.Element('trip',id=...) because the word from is a Python keyword which cannot be used outside of string declarations
        # I.e. the string 'from = d.start.edge_id' is not possible
        new = etree.Element('trip')
        new.set('id', d.id)
        new.set('type', d.agent.id)
        new.set('depart', d.depart)
        new.set('from', d.start.edge_id)
        new.set('to', d.end.edge_id)
        root.append(new)
    tree = etree.ElementTree(root)
    tree.write(filename, pretty_print=True)


# run script for demand generation
def generate():
    test_locations = create_test_locations(in_path + mapin)
    test_agents = create_test_agents(number_of_agents, test_locations)
    generate_demand_file(out_path + routesout, test_agents, number_of_days)
    veh_map_path = out_path + vehmapout
    with open(veh_map_path, 'w', newline='') as veh_map_file:
        writer = csv.writer(veh_map_file)
        writer.writerow(['trip_id', 'vehicle_id'])
        for agent in test_agents:
            for trip_id in agent.trip_ids:
                writer.writerow([trip_id, agent.id])


# Write report file
def report():
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    f = open(rep_path + rep_name, 'a')
    f.write('-------------------- Report of AGENT GENERATION --------------------\n\n')
    f.write('Name of simulation script:   ' + sys.argv[0] + '\n')
    f.write('Evaluation started at        ' + str(rep_start) +'\n')
    f.write('Evaluation ended at          ' + str(rep_end) +'\n')
    f.write('Runtime:                     ' + str(time1 - time0) + '\n\n')
    f.write('Map used:            ' + str(mapin) + '\n\n')
    f.write('Number of agents:    ' + str(number_of_agents) + '\n')
    f.write('Number of days:      ' + str(number_of_days) + '\n\n')
    f.write('Routing written to       ' + str(out_path + routesout) + '\n')
    f.write('Vehicle map written to   ' + str(in_path + vehmapout) + '\n\n')
    f.write('-------------------------- END of report ---------------------------\n\n')
    print('Report written to ' + "'" + rep_path + rep_name + "'")


# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('--inpath', dest='in_path', type=str, default='../rsc/traffic/', help='Relative path to resource file directory')
    parser.add_argument('--outpath', dest='out_path', type=str, default='../rsc/traffic/', help='Relative path to output directory')
    parser.add_argument('--agents', dest='number_of_agents', type=int, default=20, help='Number of agents')
    parser.add_argument('--parttime', dest='parttime_percentage', type=int, default=0)
    parser.add_argument('--nighttime', dest='nighttime_percentage', type=int, default=0)
    parser.add_argument('--days', dest='number_of_days', type=int, default=30, help='Number of days')
    parser.add_argument('--mapin', dest='map_input_name', type=str, default='map.xml')
    parser.add_argument('--routesout', dest='routes_output_name', type=str, default='routes.xml')
    parser.add_argument('--vehmapout', dest='vehicle_map_output_name', type=str, default='vehicle_map.csv')
    parser.add_argument('--homedistrict', dest='home_district', type=str, default='')
    parser.add_argument('--workdistrict', dest='work_district', type=str, default='')
    parser.add_argument('--reportpath', dest='report_path', type=str, default='../rsc/reports/', help='Report output directory')
    parser.add_argument('--reportname', dest='report_name', type=str, help='Set report name', default='report.txt')
    parser.add_argument('--no-report', dest='report', action='store_false', help='Do not write report')
    parser.set_defaults(report=True)
    return parser.parse_args()


def string_to_polygon_array(polygon_string):
    dist_parse = polygon_string.split(' ')
    result = []
    for pt in dist_parse:
        coords = pt.split(',')
        result.append([int(coords[0]), int(coords[1])])
    return result


if __name__ == "__main__":
    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    in_path = args.in_path
    out_path = args.out_path
    rep_path = args.report_path
    rep_name = args.report_name
    number_of_agents = args.number_of_agents
    parttime_percentage = args.parttime_percentage/100
    nighttime_percentage = args.nighttime_percentage/100
    if parttime_percentage + nighttime_percentage > 1:
        raise ValueError("Invalid percentages of workers specified.")
    number_of_days = args.number_of_days
    mapin = args.map_input_name
    routesout = args.routes_output_name
    vehmapout = args.vehicle_map_output_name

    home_district = District(string_to_polygon_array(args.home_district))
    work_district = District(string_to_polygon_array(args.work_district))
    districts = [home_district, work_district]

    # Global report variables
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Generate demand
    generate()

    # Write report except flag --no-report is set
    if args.report:
        report()
