from lxml import etree
import xml.etree.ElementTree as ET
import random
import math
import time
import argparse
from tqdm import tqdm
import sys
from datetime import datetime
import os
import csv



# Main method
def attack():
    # Read 
    knowledge_tree = etree.parse(rsc_path + 'knowledge/' + input_file_name)
    knowledge_root = knowledge_tree.getroot()
    knowledge_transactions = knowledge_root[0] # transactions are first element in attacker xml tree

    global remaining_transactions
    remaining_transactions = len(knowledge_transactions.getchildren()) # number of transactions in attacker knowledge
    global rep_transactions
    rep_transactions = len(knowledge_transactions.getchildren())
    global rep_vehicles
    rep_vehicles = len(list(knowledge_tree.getiterator('wallet')))

    times = open(rsc_path + 'knowledge/detector_times.csv', 'r', newline='')
    timereader = csv.reader(times)
    timedata = list(timereader)


    maxtimetonext = 21
    while len(knowledge_transactions) > 0:
        trip = construct_trip(knowledge_transactions, timedata, maxtimetonext)
        print('Found trip of length ' + str(len(trip)) + ':')
        print(trip)
        



# Constructs a trip based on knowledge XML file and time CSV file
# Output: Returns trip as a list of tuples ['detector','time']
def construct_trip(knowledge, times, maxtimetonext):
    trip = []
    deleted_ids = []

    # Set first 
    r = random_int(0,min(10,len(knowledge)))
    trip.append([knowledge[r].get('detector'),knowledge[r].get('time')])
    deleted_ids.append(knowledge[r].get('id'))
    current_detector = knowledge[r].get('detector')
    current_time = knowledge[r].get('time')
    knowledge.remove(knowledge[r])

    maxlength = 7
      
    next_id = next_step(current_detector, current_time, knowledge, times, maxtimetonext)
    while not next_id == 0 and len(trip) < maxlength:
        for child in knowledge:
            if child.get('id') == next_id:
                trip.append([child.get('detector'),child.get('time')])
                current_detector = child.get('detector')
                current_time = child.get('time')
                knowledge.remove(child)
        next_id = next_step(current_detector, current_time, knowledge, times, maxtimetonext)
    
    return trip


    

# Input:
# - detector:   current detector name
# - cure
def next_step(detector, current_time, knowledge, timedata, min):
    success = False
    result_id_list = []
    # This for loop returns a list of possible ids of transactions which realise the minimum deviation from the expected travel time
    for child in knowledge:
        if not child.get('detector') == detector:
            # Search for detector in the neighbourhood of DETECTOR
            if not time_between_detectors(detector, child.get('detector'), timedata) == 'x' and float(time_between_detectors(detector, child.get('detector'), timedata)) > 0:
                # mintime is the minimal time that it takes to reach child.get('detector') from detector
                mintime = time_between_detectors(detector, child.get('detector'), timedata)

                diff = int(child.get('time'))-float(current_time)
                if diff >= float(mintime):
                    if min >= diff-float(mintime):
                        success = True
                        min = diff-float(mintime)
                        result_id_list = [child.get('id')]
                    elif min == diff-float(mintime):
                        success = True
                        min = diff-float(mintime)
                        result_id_list.append(child.get('id'))
    if success:
        return result_id_list[random_int(0,len(result_id_list))]
    else:
        return 0



# Returns the time between departure and destination detector based on times data list
def time_between_detectors(departure, destination, timedata):
    row_idx = 0
    col_idx = 1
    while not timedata[row_idx][0] == departure:
        row_idx += 1
    while not timedata[0][col_idx] == destination:
        col_idx += 1
    return timedata[row_idx][col_idx]



# Returns random integer in interval [lower,upper]
# If lower bound = upper boud, this function returns the bounds
# Personally, I have no background knowledge on how random this is
def random_int(lower, upper):
    if(lower < upper):
        rand_int = random.randrange(lower, upper)
    else:
        rand_int = lower
    return rand_int




# Write report file
def report():
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    f = open(rsc_path + 'reports/' + rep_name, 'a')
    f.write('-------------------- Report of RANDOM ATTACK --------------------\n\n')
    f.write('Name of attack script:   ' + sys.argv[0] + '\n')
    f.write('Attack started at        ' + str(rep_start) +'\n')
    f.write('Attack ended at          ' + str(rep_end) +'\n')
    f.write('Runtime:                 ' + str(time1 - time0) + '\n\n')
    f.write('Attacker knowledge file is   ' + "'" + rsc_path + 'knowledge/' + input_file_name + "'\n")
    f.write('- of file size               ' + str(os.path.getsize(rsc_path + 'knowledge/' + input_file_name)) + ' bytes\n\n')
    f.write('Output file is   ' + "'" + rsc_path + 'attacks/' + output_file_name + "'\n")
    f.write('- of file size   ' + str(os.path.getsize(rsc_path + 'attacks/' + output_file_name)) + ' bytes\n\n')
    f.write('Random seed was ' + str(seed) + '\n\n')
    f.write('Number of transactions:   ' + str(rep_transactions) + '\n')
    f.write('Number of vehicles:       ' + str(rep_vehicles) + '\n\n')
    f.write('Transaction assignment fails:   ' + str(failed_assignments) + '\n')
    f.write('Unassigned transactions:        ' + str(remaining_transactions) + '\n\n')
    f.write('-------------------- END of report --------------------\n\n')
    print('Report written to ' + "'" + rsc_path + 'reports/' + rep_name + "'")



# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('-p', '--path', dest='rsc_path', type=str, help='Relative path to resource files', default='../rsc/')
    parser.add_argument('-k', '--knowledge', dest='input_file_name', type=str, help='Specify attacker knowledge to be used for attack', required=True)
    parser.add_argument('-o', '--output', dest='output_file_name', type=str, help='Set output xml file name', default='random.xml')
    parser.add_argument('-s', '--seed', dest='seed', type=int, help='Set random seed for random attack')
    parser.add_argument('-r', '--report', dest='report_name', type=str, help='Set report name', default='report.txt')
    return parser.parse_args()



# Run main method on start
if __name__ == "__main__":
    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    rsc_path = args.rsc_path
    input_file_name = args.input_file_name
    output_file_name = args.output_file_name
    rep_name = args.report_name
    if args.seed is not None:
        seed = args.seed
    else:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)

    # Global report variables
    rep_transactions = 0
    rep_vehicles = 0
    failed_assignments = 0
    remaining_transactions = 0
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Attack and report
    attack()
    #report()