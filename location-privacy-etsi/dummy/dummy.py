import os
import sys
import inspect
import optparse
from tqdm import tqdm

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    sys.path.append('../agent')
else:
    sys.exit("please declare environment varibale 'SUMO_HOME")


from sumolib import checkBinary
import traci
from lxml import etree

#import agent_generation

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


def run(vehicle_map):
    # generate mapping detector -> junction/cost
    detectors_tree = etree.parse(rsc_path + 'traffic/dummy-detectors.add.xml')
    detectors_root = detectors_tree.getroot()
    junction_detector_dict = {}
    # need to find a way to better read xml or better iterate
    # first entry is broken / the root
    for detector in detectors_root.iter():
        junction_name = str(detector.get("lane"))[2:4]
        detector_id = detector.get("id")
        # junction_name is "None" because the first entry is broken
        if (junction_name != "ne"):
            if junction_name not in junction_detector_dict:
                junction_detector_dict[junction_name] = [detector_id]
            else:
                junction_detector_dict[junction_name].append(detector_id)

    # better way 
    # possibility to change format to <junction><detector></detector>...</junction>
    only_junctions = etree.Element("junctions")
    for junction, detectors in junction_detector_dict.items():
        det_string = ""
        for d in detectors:
            det_string += d + " "
        # Kosten über Zoning
        etree.SubElement(only_junctions, "junction", name=junction, detectors=det_string[:-1], cost="1")
    
    tree = etree.ElementTree(only_junctions)
    tree.write(rsc_path + 'traffic/junctions.xml', pretty_print=True)


    # run simulation and generate detector data
    root = etree.Element("challenger")
    knowledges = etree.SubElement(root, "transactions")
    step = 0
    enumerator = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        # advance traci
        traci.simulationStep()
        det_list = traci.inductionloop.getIDList()
        for id in det_list:
            det_vehs = traci.inductionloop.getLastStepVehicleIDs(id)
            for veh in det_vehs:
                # vehicle = trip_id => agent has list of trips => find agent by vehicle/trip_id
                agent = vehicle_map[veh] # vehicle_map.get(veh, "default_value")
                etree.SubElement(knowledges, "transaction", id=str(enumerator), detector=id, vehicle=agent, trip=veh, time=str(step))
                enumerator += 1

        step += 1
    
    
    # remove entries that are one timestep different on the same detector with the same car
    bad_entries = []
    for i in tqdm(range(len(knowledges)-1),desc='Removing bad entries'):
        testagainst_time = int(knowledges[i].get("time"))
        testagainst_detector = knowledges[i].get("detector")
        testagainst_vehicle = knowledges[i].get("vehicle")
        for j in range(i+1, len(knowledges)):
            time = int(knowledges[j].get("time"))
            if (time >= testagainst_time+1):
                break
            if (knowledges[j].get("detector") == testagainst_detector and knowledges[j].get("vehicle") == testagainst_vehicle and time-1 == testagainst_time):
                bad_entries.append(knowledges[j])
    
    for bad in bad_entries:
        knowledges.remove(bad)

    # cross-reference junctions with detector data to generate challenger knowledge
    junctions = etree.parse(rsc_path + 'traffic/junctions.xml')
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
                    if vehicle_id not in wallet_dict:
                        wallet_dict[vehicle_id]=[int(junction_cost)]
                    else:
                        wallet_dict[vehicle_id].append(int(junction_cost))

                    # trip stuff
                    trip_id = data.get("trip")
                    transaction_details = {
                            "id": data.get("id"),
                            "cost": int(junction_cost),
                            "trip": data.get("trip"),
                            "agent": data.get("vehicle"),
                            "time": data.get("time")
                        }
                    if trip_id not in trip_dict:
                        trip_dict[trip_id]=[data.get("id")]
                        trip_dict[trip_id]=[transaction_details]
                    else:
                        trip_dict[trip_id].append(data.get("id"))
                        trip_dict[trip_id].append(transaction_details)

    #print("Do wallets ...")
    wallets = etree.SubElement(root, "wallets")
    for vehicle, costs in wallet_dict.items():
        wallet_cost_total = 0
        for c in costs:
            wallet_cost_total += c
        etree.SubElement(wallets, "wallet", vehicle=vehicle, wallet_cost=str(wallet_cost_total))

    print("do trips")
    trips = etree.SubElement(root, "trips")
    for trip, transactions in trip_dict.items():
        current_trip = etree.SubElement(trips, "trip", trip_id=trip)
        trip_cost_total = 0
        for transaction in transactions:
            trip_cost_total += transaction["cost"]
            etree.SubElement(current_trip, "transaction", 
            id=transaction["id"], 
            cost=str(transaction["cost"]), 
            agent=transaction["agent"],
            time=transaction["time"])
        current_trip.set("trip_cost", str(trip_cost_total))
    # change structure of challenger.xml:
    # knowledge - wallets - wallet - trips - trip - transaction
    # run simulation / get all transactions
    # create wallets and trips through given vehicle map
    # sort transactions according to trip-id to make this feasible
    # just go over sorted list, generate a new "trip" with id and agent for every new found trip and move the entry there?
    # def sortchildrenby(parent, attr):
    #     parent[:] = sorted(parent, key=lambda child: child.get(attr))

    # sortchildrenby(knowledges, "trip")
    
    # copy wallet stuff
    # structure sth like: <trip=id><transaction/>...<transaction/><trip/>...

    metainfo = etree.SubElement(root, "metainfo")
    etree.SubElement(metainfo, "allTransactions", total_transactions=str(total_transactions), total_cost=str(total_cost))

    # write challenger knowledge to xml
    tree = etree.ElementTree(root)
    tree.write(rsc_path + 'knowledge/' + 'challenger-new.xml', pretty_print=True)

    # Generate attacker knowledge
    challenger_root = root
    attacker_root = etree.Element("attacker")
    attacker_transactions = etree.SubElement(attacker_root, "transactions")
    for child in tqdm(knowledges,desc='Generating attacker knowledge'):
        # dirty copying of attributes, probably okay, I guess
        etree.SubElement(attacker_transactions, "transaction", id=child.get('id'), detector=child.get('detector'), time=child.get('time'), junction=child.get('junction'), cost=child.get('cost'))
    attacker_root.append(wallets)
    attacker_root.append(metainfo)
    tree = etree.ElementTree(attacker_root)
    tree.write(rsc_path + 'knowledge/' + 'attacker-new.xml', pretty_print=True)


    traci.close()
    sys.stdout.flush()


if __name__ == "__main__":
    options = get_options()
    rsc_path = '../rsc/'

    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    vehicle_map = None #agent_generation.generate()
    traci.start([sumoBinary, "-c", rsc_path + 'traffic/dummy-tls.sumocfg', "--tripinfo-output", rsc_path + 'traffic/tripinfo.xml'])

    run(vehicle_map)