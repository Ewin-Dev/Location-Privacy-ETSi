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

    # Assigning a random transaction to a wallet might fail if transaction_cost > wallet_cost
    # Random attack uses a threshold to determine the number of trials for assigning a transaction to a wallet
    threshold = remaining_transactions

    # Create vehicle-wallet dictionary from wallet tags in attacker.xml to keep track of total costs
    # Useful to subtract transaction costs from total costs
    dict = {}
    for child in knowledge_tree.getiterator('wallet'):
        dict[child.get('vehicle')] = child.get('wallet_cost')

    # Initialise output XML file root
    output_root = etree.Element('attack')

    # Iterate over all vehicles
    for vehicle in tqdm(list(dict.keys()),desc='Filling wallet'):
        # For every vehicle, iterate threshold many times and abort if remaining wallet costs are 0
        iterator = 0

        while iterator < threshold and int(dict[vehicle]) > 0:
            # Randomly choose a transaction
            transaction_to_assign_no = random_int(0,remaining_transactions)
            transaction_to_assign = knowledge_transactions[transaction_to_assign_no]

            # If transaction fits into the vehicle’s wallet
            if int(transaction_to_assign.get('cost')) <= int(dict[vehicle]):
                # Reduce wallet costs by costs of assigned transaction
                dict[vehicle] = str(int(dict[vehicle]) - int(transaction_to_assign.get('cost')))

                # Append tag to XML file by dirty copying of attributes
                etree.SubElement(output_root, "transaction", detector=transaction_to_assign.get('detector'), vehicle=vehicle, time=transaction_to_assign.get('time'), junction=transaction_to_assign.get('junction'), cost=transaction_to_assign.get('cost'))

                # Remove transaction from the list
                remaining_transactions -= 1
                knowledge_transactions.remove(knowledge_transactions[transaction_to_assign_no])

            # Else increase fail counter for report purposes
            else:
                global failed_assignments
                failed_assignments+=1
            iterator+=1
    
    # Write attack output file
    global output_tag
    output_tag = str(datetime.now().strftime('%d%m%y-%H%M%S'))
    tree = etree.ElementTree(output_root)
    tree.write(rsc_path + 'attacks/' + output_file_name, pretty_print=True)



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



# Returns random integer in interval [lower,upper]
# If lower bound = upper boud, this function returns the bounds
# Personally, I have no background knowledge on how random this is
def random_int(lower, upper):
    if(lower < upper):
        rand_int = random.randrange(lower, upper)
    else:
        rand_int = lower
    return rand_int



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
    report()