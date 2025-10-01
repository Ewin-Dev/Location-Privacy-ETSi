# coding: utf-8
import os
import sys
import argparse
from tqdm import tqdm
import time
from datetime import datetime
import xml.etree.ElementTree as etree
from sumolib import checkBinary
import traci
import csv


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    sys.path.append('../agent')
else:
    sys.exit("please declare environment varibale 'SUMO_HOME")




def run(vehicle_map):
    # using the detectors.add.xml file to extract all relevant junctions 
    detectors_tree = etree.parse(in_path + detector_file)
    detectors_root = detectors_tree.getroot()
    junction_detector_dict = {}
    
    for detector in detectors_root.iter():
        # getting the name of the detector from the detectors.add.xml file
        index_of_lane = str(detector.get("lane")).find('_')
        detector_name = str(detector.get("lane"))[0:index_of_lane]
        # finding the last letter in the detectorname to specify on which junction the detector is placed
        last_letter = 0
        for i in range(0, len(detector_name)):   
            if (detector_name[i].isalpha()):
                last_letter = i

        # junction names are a subset of the detector name like A18A19 as detector name, means A19 is the junction
        junction_name = detector_name[last_letter:]
        detector_id = detector.get("id")
        # first entry is broken, there we need to filter the junction_name "None"
        # generating a mapping of junction -> all detectors at this junction
        if (junction_name != "n"):
            if junction_name not in junction_detector_dict:
                junction_detector_dict[junction_name] = [detector_id]
            else:
                junction_detector_dict[junction_name].append(detector_id)


    only_junctions = etree.Element("junctions")
    for junction, detectors in junction_detector_dict.items():
        det_string = ""
        for d in detectors:
            det_string += d + " "
        # Cost for every junction is simply 1 at the moment
        # Further Work: Implementing a function that gets a more reasonable cost for every junction, depending on some factors like position of the junction
        etree.SubElement(only_junctions, "junction", name=junction, detectors=det_string[:-1], cost="1")
    
    tree = etree.ElementTree(only_junctions)
    tree.write(in_path + junction_file)

    # running simulation and generate detector data
    root = etree.Element("challenger")
    knowledges = etree.SubElement(root, "transactions")
    step = 0
    enumerator = 0
    print('Running Simulation ...')
    while traci.simulation.getMinExpectedNumber() > 0:
        # advance traci
        traci.simulationStep()
        # getting all detectors (induction loops) that are in the simulation
        det_list = traci.inductionloop.getIDList()
        for id in det_list:
            # getting every vehicle that was seen by every detector in the step
            det_vehs = traci.inductionloop.getLastStepVehicleIDs(id)
            for veh in det_vehs:
                # generating a transaction for every vehicle that was seen by any detector
                # every transaction contains: id, which detector found the vehicle, the vehicle (agent) id, the trip id, at which time step the transaction took place
                # check if detector is a E1 detector
                if (id.startswith('e1det')):
                    etree.SubElement(knowledges, "transaction", id=str(enumerator), detector=id, vehicle=vehicle_map[veh], trip=veh, time=str(step))
                    enumerator += 1

        step += 1

    # often a detector will find the same vehicle at timestep x and also at timestep x+1 and sometimes even at x+2
    # at this point those entries are detected
    # if you want to see/use every transaction, comment out lines 88-117
    bad_entries = []
    for i in tqdm(range(len(knowledges)-1),desc='Detecting bad entries'):
        testagainst_time = int(knowledges[i].get("time"))
        testagainst_detector = knowledges[i].get("detector")
        testagainst_vehicle = knowledges[i].get("vehicle")
        for j in range(i+1, len(knowledges)):
            time = int(knowledges[j].get("time"))
            # skip entries which are farther away to minimize complexity here
            # if this does not happen we have O(n²) with n being the number of transactions
            if (time > testagainst_time+1):
                break
            if (knowledges[j].get("detector") == testagainst_detector and knowledges[j].get("vehicle") == testagainst_vehicle and time-1 == testagainst_time):
                bad_entries.append(knowledges[j])

    # removing the detected bad entries
    def sortchildrenby(parent, attr):
        parent[:] = sorted(parent, key=lambda child: child.get(attr))
    def sortchildrenbyreverse(parent, attr):
        parent[:] = sorted(parent, key=lambda child: child.get(attr), reverse=True)

    for i in tqdm(range(int(len(bad_entries)/2)), desc='Removing bad entries 1/2'):
        knowledges.remove(bad_entries[i])
        bad_entries.remove(bad_entries[i])

    sortchildrenbyreverse(root, 'id')

    for bad in tqdm(bad_entries, desc='Removing bad entries 2/2'):
        knowledges.remove(bad)

    sortchildrenby(root, 'id')

    
    # at this point we have a lot of transactions, where we only know at which detector they took place and a file that has a junction and a cost assosiated to every detector
    # cross-reference junctions with detector data to generate challenger knowledge
    junctions = etree.parse(in_path + junction_file)
    total_transactions = 0
    total_cost = 0
    wallet_dict = {}
    trip_dict = {}
    for data in tqdm(knowledges,desc='Cross-referencing data'):
        for junction in junctions.iter():
            if (junction.get("detectors") is not None):
                if(data.get("detector") in junction.get("detectors")):
                    junction_cost = junction.get("cost")
                    data.set("junction", junction.get("name"))
                    data.set("cost", junction_cost)
                    total_cost += int(junction_cost)
                    total_transactions += 1
                    vehicle_id = data.get("vehicle")
                    # saving some details for every wallet, so that we can later save every wallet with the assosiated transactions, which helps evaluating attacks
                    wallet_transaction_details = {
                        "id": data.get("id"),
                        "cost": int(junction_cost)
                    }
                    if vehicle_id not in wallet_dict:
                        wallet_dict[vehicle_id]=[wallet_transaction_details]
                    else:
                        wallet_dict[vehicle_id].append(wallet_transaction_details)

                    # saving most transaction details of every trip, to have an easier time evaluating later
                    trip_id = data.get("trip")
                    trip_transaction_details = {
                            "id": data.get("id"),
                            "cost": int(junction_cost),
                            "trip": data.get("trip"),
                            "agent": data.get("vehicle"),
                            "junction": data.get("junction"),
                            "detector": data.get("detector"),
                            "time": data.get("time")
                        }
                    if trip_id not in trip_dict:
                        trip_dict[trip_id]=[trip_transaction_details]
                    else:
                        trip_dict[trip_id].append(trip_transaction_details)

    # generating wallet information in the xml, also calculating the total wallet cost for every wallet
    wallets = etree.SubElement(root, "wallets")
    for vehicle, wallet_transactions in wallet_dict.items():
        current_wallet = etree.SubElement(wallets, "wallet", agent=vehicle)
        wallet_cost_total = 0
        for t in wallet_transactions:
            wallet_cost_total += t["cost"]
            etree.SubElement(current_wallet, "wallet_transaction", id=t["id"])
        current_wallet.set("total_wallet_cost", str(wallet_cost_total))


    # generating trip information in the xml, also calculates total trip cost
    trips = etree.SubElement(root, "trips")
    for trip, transactions in tqdm(trip_dict.items(), desc="Generating Trip Data"):
        current_trip = etree.SubElement(trips, "trip", trip_id=trip)
        trip_cost_total = 0
        trip_agent = ""
        for transaction in transactions:
            trip_cost_total += transaction["cost"]
            trip_agent = transaction["agent"]
            etree.SubElement(current_trip, "trip_transaction", 
                id=transaction["id"], 
                cost=str(transaction["cost"]), 
                junction=transaction["junction"],
                detector=transaction["detector"],
                time=transaction["time"])
        current_trip.set("agent", trip_agent)
        current_trip.set("trip_cost", str(trip_cost_total))

    # generating some meta info in the xml; number of total transactions and the total cost (which currently equal to the number of transactions but should change in the future)
    metainfo = etree.SubElement(root, "metainfo")
    etree.SubElement(metainfo, "allTransactions", total_transactions=str(total_transactions), total_cost=str(total_cost))

    # write challenger knowledge to xml
    tree = etree.ElementTree(root)
    tree.write(out_path + coutput)

    # Generate attacker knowledge
    attacker_root = etree.Element("attacker")
    attacker_transactions = etree.SubElement(attacker_root, "transactions")
    for child in tqdm(knowledges,desc='Generating attacker knowledge'):
        # dirty copying of attributes, probably okay, I guess
        etree.SubElement(attacker_transactions, "transaction", id=str(child.get('id')), detector=child.get('detector'), time=str(child.get('time')), junction=child.get('junction'), cost=str(child.get('cost')))
    attacker_root.append(wallets)
    attacker_root.append(metainfo)
    tree = etree.ElementTree(attacker_root)
    tree.write(out_path + aoutput)


    traci.close()
    sys.stdout.flush()



# Write report file
def report():
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    f = open(rep_path + rep_name, 'a')
    f.write('-------------------- Report of SIMLUATION --------------------\n\n')
    f.write('Name of simulation script:   ' + sys.argv[0] + '\n')
    f.write('Seed for this simulation was:' + str(12345) + '\n')
    f.write('Evaluation started at        ' + str(rep_start) +'\n')
    f.write('Evaluation ended at          ' + str(rep_end) +'\n')
    f.write('Runtime:                     ' + str(time1 - time0) + '\n\n')
    f.write('GUI used:             ' + str(args.gui) + '\n')
    f.write('sumocfg file:         ' + "'" + in_path + sumocfg + "'\n")
    f.write('Tripinfo written to   ' + "'" + in_path + tripinfo_file + "'\n\n")
    f.write('Challenger knowledge written to   ' + "'" + out_path + coutput + "'\n")
    f.write('- of file size                    ' + str(os.path.getsize(out_path + coutput)) + ' bytes\n\n')
    f.write('Attacker knowledge written to     ' + "'" + out_path + aoutput + "'\n")
    f.write('- of file size                    ' + str(os.path.getsize(out_path + aoutput)) + ' bytes\n\n')
    
    f.write('-------------------- END of report --------------------\n\n')
    print('Report written to ' + "'" + rep_path + rep_name + "'")



# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('--inpath', dest='in_path', type=str, default='../rsc/traffic/', help='Relative path to resource file directory')
    parser.add_argument('--outpath', dest='out_path', type=str, default='../rsc/knowledge/', help='Relative path to output directory')
    parser.add_argument('--cout', dest='coutput', type=str, required=True, help='Challenger xml file output name')
    parser.add_argument('--aout', dest='aoutput', type=str, required=True, help='Attacker xml file output name')
    parser.add_argument('--junctions', dest='junctions', type=str, required=True, help='Junction xml file')
    parser.add_argument('--detectors', dest='detectors', type=str, required=True, help='Detectors add.xml file')
    parser.add_argument('--seed', dest='seed', type=int, help='Seed for this simulation')
    parser.add_argument('--tripinfo', dest='tripinfo', type=str, default='tripinfo.xml', help='Name of tripinfo-output xml file')
    parser.add_argument('--sumocfg', dest='sumocfg', type=str, required=True)
    parser.add_argument('--gui', dest='gui', action='store_true', help='Run command line version of sumo')
    parser.add_argument('--nogui', dest='gui', action='store_false', help='Run command line version of sumo')
    parser.set_defaults(feature=False)
    parser.add_argument('--reportpath', dest='report_path', type=str, default='../rsc/reports/', help='Report output directory')
    parser.add_argument('--reportname', dest='report_name', type=str, help='Set report name', default='report.txt')
    parser.add_argument('--no-report', dest='report', action='store_false', help='Do not write report')
    parser.set_defaults(report=True)
    return parser.parse_args()



if __name__ == "__main__":
    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    in_path = args.in_path
    out_path = args.out_path
    rep_path = args.report_path
    rep_name = args.report_name
    coutput = args.coutput
    aoutput = args.aoutput
    seed = args.seed
    sumocfg = args.sumocfg
    detector_file = args.detectors
    junction_file = args.junctions
    tripinfo_file = args.tripinfo
    rep_name = args.report_name

    # Global report variables
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Read vehicle map
    vehicle_map = dict()
    with open(in_path + 'vehicle_map.csv') as veh_map_file:
        reader = csv.reader(veh_map_file)
        for row in reader:
            vehicle_map[row[0]] = row[1]

    # Run the simulation
    if args.gui:
        sumoBinary = checkBinary('sumo-gui')
    else:
        sumoBinary = checkBinary('sumo')

    traci.start([sumoBinary, "-c", in_path + sumocfg, "--tripinfo-output", in_path + tripinfo_file, '--no-step-log'])

    run(vehicle_map)
    # Write report except flag --no-report is set
    if args.report:
        report()
