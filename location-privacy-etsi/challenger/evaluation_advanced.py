import argparse
import os
import sys
import time
import networkx as nx
from lxml import etree
import xml.etree.ElementTree as ET
import random
from copy import copy
from tqdm import tqdm
from datetime import datetime






#returns the avg. percentage of correct transactions in trips
def challengerTrips():
    challenger_trips = root_challenger_knowlege[2]
    per = set([]) #set with the success percentage of the trips
    tripList =  []
    #create a list with sets, the sets contain the ids from the trips
    for i in range(0, len(challenger_trips)):
            challenger_trip  =  challenger_trips[i]
            
            ids=set([])
            
            for j in range(0, len(challenger_trip)):
                ids.add(int(challenger_trip[j].attrib['id']))
            tripList.append(ids)

    #compare the attacker trips with the challenger trips
    for trip in tqdm(root_attackere[0], desc="Challenger Trips"): 
        k = 0
        str_list = trip.attrib['ids'].split(' ')
        usedTrips = set(map(int, str_list))

        #find the best trip where the percentage is the highest 
        for i in range(0, len(tripList)):
            ids  =  tripList[i]

            # use Jaccard index to compare the trips
            ktemp = len(usedTrips&ids) / float(len(usedTrips|ids)) * 100
            
            if ktemp>k:
                k = ktemp
            if k == 100:
                break

        per.add(k)  
    #print("Trips %:",  round(sum(per) / len(per),2))  
    return (round(sum(per) / len(per),2))

#returns the avg. percentage of correct transactions in wallets
def challengerWallets():
    
    per = [] #list with the success percentage of the wallets
    walletList =  [] #list with sets, the sets cotain the wallet ids

    #create a list with a sets with ids from wallets
    for i in root_challenger_knowlege.iter('wallet'):

            ids=set([])  
            for j in i.iter('wallet_transaction'):
                ids.add(int(j.attrib['id']))
            walletList.append(ids)

     #compare the attacker trips with the challenger trips
    for trip in tqdm(root_attackere[1], desc="Challenger Walltes"): 
        k = 0
        str_list = trip.attrib['ids'].split(' ')
        usedTrips = set(map(int, str_list))

        #find the best wallet for the attacker wallet
        for i in range(0, len(walletList)):

            ids  =  walletList[i]
            
            # use Jaccard index
            ktemp = len(usedTrips & ids) / float(len(usedTrips | ids)) * 100
            if ktemp>k:
                k = ktemp
        per.append(k)  
    
    return (round(sum(per) / len(per),2))   
    
    


# Write report file
def report():
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    f = open('reports/' + rep_name, 'a')
    f.write('-------------------- Report of ADVANCED EVALUATION --------------------\n\n')
    f.write('Name of evaluation script:   ' + sys.argv[0] + '\n')
    f.write('Evaluation started at        ' + str(rep_start) +'\n')
    f.write('Evaluation ended at          ' + str(rep_end) +'\n')
    f.write('Runtime:                     ' + str(time1 - time0) + '\n\n')
    f.write('Measure of success:     Correctly assigned transactions to wallets or trips with Jaccard index' +"\n")
    f.write('Number of transactions: ' + str(rep_transactions) + '\n')

    f.write('Challenger knowledge file is   ' + "'" + knowledge_file_name + "'\n")
    f.write('- of file size                 ' + str(os.path.getsize(knowledge_file_name)) + ' bytes\n\n')

    f.write('Avg. percentage of right transactions in trips: ' + str(resultTrips) + '%.\n\n')
    f.write('Avg. percentage of right transactions in wallets: ' + str(resultWallets) + '%.\n\n')
    
    f.write('-------------------- END of report --------------------\n\n')
    print('Report written to ' + "'" + 'reports/' + rep_name + "'")



# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('-p', '--path', dest='rsc_path', type=str, help='Relative path to resource files', default='../rsc/')
    parser.add_argument('-c', '--challenger', dest='knowledge_file_name', type=str, help='Which attacker knowledge file to use?', required=True)
    parser.add_argument('-a', '--attacker', dest='eval_file_name', type=str, help='Set attacker output file', required=True)
    parser.add_argument('-r', '--report', dest='report_name', type=str, help='Set report name', default='report.txt')
    return parser.parse_args()

def main():
    global root_challenger_knowlege, root_attackere, resultTrips, resultWallets, rep_transactions
   
    tree_challenger_knowlege = ET.parse(str(knowledge_file_name))
    root_challenger_knowlege = tree_challenger_knowlege.getroot()
   

    tree_attacker = ET.parse(str(eval_file_name))
    root_attackere = tree_attacker.getroot()
    resultTrips = challengerTrips()
    resultWallets =challengerWallets()

    for i in tree_challenger_knowlege.iter('allTransactions'):
       rep_transactions = i.attrib["total_transactions"]



# Run main method on start
if __name__ == "__main__":
    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    rsc_path = args.rsc_path
    knowledge_file_name = args.knowledge_file_name
    eval_file_name = args.eval_file_name
    rep_name = args.report_name
    
    # Global report variables
    rep_transactions = 0
    rep_vehicles = 0
    rep_success = 0
    output_tag = None
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    main()
    report()
