import argparse
import os
import sys
import time
import networkx as nx
import xml.etree.ElementTree as ET
import random
from copy import copy
from tqdm import tqdm
from datetime import datetime

#possible trip that was found with all the informations 
class Trip:
  def __init__(self, vehicle, timeStart, timeEnd, duration, cost, trip, used, deltaSum):
    self.vehicle = vehicle
    self.timeStart = timeStart
    self.timeEnd = timeEnd
    self.duration = duration
    self.cost= cost
    self.trip = trip #String with all Edges
    self.used = used    #int list with all ids that are used in this trip
    self.deltaSum = deltaSum    # the deviation from the avg. times from every edge in this trip


   




#generates a graph with conectet detectors (nodes are the detectors). 
def generateGraph():
    
    tree_detectors = ET.parse(rsc_path + 'knowledge/' + simulated_times_file)
    root_detectors = tree_detectors.getroot()

    for detector in root_detectors.iter('route'):

        #nodes
        fromDetector = detector.attrib['fromDetector']  
        toDetector = detector.attrib['toDetector'] 

        #weights
        avg = float(detector.attrib['avg'])
        minTime = float(detector.attrib['minTime'])
        maxTime = float(detector.attrib['maxTime'])

        #create edge
        DG.add_edge(fromDetector, toDetector, avg=avg, min=minTime, max=maxTime)




#find the trips with the best deviation from the avg. times

def findTrips():

    lastDetector = ""

    t=0 #time

    x=0 #used for the agend names


    #go trough every transaction, and try to find a possible trip
    for i in range(0, len(transactions_attackert_knowlege)):

        #startpoint of the trip
        transaction= transactions_attackert_knowlege[i]
        first= True

        #string with all detector names, that are used in this trip
        result = ""        
       
        #id of the transaction
        id =  int(transaction.attrib['id'])

        #used to start the inner for loop at the right transaction
        inner_start=i

        #only search for a trip if the start transaction was't used before   
        if not id in usedTrans:

            #get the informations from this startpoint
            lastDetector = transaction.attrib['detector']      
            detector = transaction.attrib['detector']   
            timeTrans = int(transaction.attrib['time'])
            cost = int(transaction.attrib['cost'])

            # remember start time
            timeStart = timeTrans            

            #was at least one plausible trip edge found  
            found = False

            #local used transaction ids
            locUsed = []

            # the deviation from the avg. times fome every edge in this trip
            deltaSum = 0

            # list with every delta from this trip
            deltaSumArr=[]

            # array with the best deviations
            bestDeltas = []
           

            while(True):

                #check all outgoing edges from the detector
                for u, v, data in DG.out_edges(lastDetector, data=True):
                    
                    #get the weights
                    avg = data.get('avg')
                    min = data.get('min') 
                    max = data.get('max')
                    
                    
                    #find suitable transaction 
                    for  j in range(inner_start+1 , len(transactions_attackert_knowlege)):

                        #get the informations from the possible next point    
                        transaction_inner = transactions_attackert_knowlege[j]
                        detector_inner = transaction_inner.attrib['detector']
                        id_inner = int(transaction_inner.attrib['id'])
                        timeTrans_inner = int(transaction_inner.attrib['time'])

                        #difference between arrival and departure
                        travel_time = timeTrans_inner - timeTrans

                        # get out the loop if the transactions are to far away
                        if travel_time > max * 1.2 and travel_time > 3 * avg:
                            break

                        # check if id is used and the detector is the right
                        if (detector_inner == v and travel_time >= 0 and travel_time <= 4 * avg and travel_time >= min*0.8  and id_inner not in usedTrans):
                            
                            #check if differece is plausible
                            if  travel_time >= 0 and travel_time >= min*0.8 and travel_time <= max * 1.2: 
                                
                                # calculate the differnce between the avg. from the simulated times and this
                                deltaTemp = abs(avg - travel_time)
                                    
                                #if the new difference is better than the worst (last ) in the array
                                # update the array and at the better difference and remove the worst one
                                if (detector_inner == v and (not found or deltaTemp < bestDeltas[-1][2] )): 
                                    
                                    found = True

                                    bestDeltas.append([id_inner,transaction_inner,deltaTemp,j])
                                    #sort after the deltaTemp
                                    bestDeltas.sort(key = lambda c:c[2])
                                    
                                    #cut the array. only the n best trips will be saved 
                                    bestDeltas=bestDeltas[0:2]
                
                #get out the while loop if no trip was found             
                if not found:
                    break
                else:
                
                    #add the values for the first trip node.
                    if first:
                        result = detector[6:-2] #only saves the edge name
                        first = False
                        locUsed.append(id)
                        usedTrans.add(id)
                    
                    #get one random entry from the array with the best values    
                    outcome = random.randint(0,len(bestDeltas)-1)
                     
                    delta = bestDeltas[outcome][2] 
                    transTemp = bestDeltas[outcome][1]  
                    inner_start = bestDeltas[outcome][3]

                    #update last the detector                      
                    lastDetector= transTemp.attrib['detector']  
                    t=int(transTemp.attrib['time'])
                    cost2 = int(transTemp.attrib['cost'])
                    
                    #remeber used id
                    k=int(bestDeltas[outcome][0])
                    locUsed.append(k)
                    usedTrans.add(k)

                    #calculate delta avg.
                    deltaSumArr =  deltaSumArr + [delta]
                    deltaSumAvg=sum(deltaSumArr)/len(deltaSumArr)
                    
                    # remove the lane and e1det
                    result = result + " " + lastDetector[6:-2]

                    #update costs
                    cost = cost + cost2
                    
                    #update timestamp from the new detector
                    timeTrans = t

                    #reset
                    delta = -1 
                    found = False
                    bestDeltas = []
          
              

            #save trip when no new plausible transaction were found     
            if result != "":            
                results.append(Trip("agent"+str(x),timeStart,t, t-timeStart, cost, set(result.split()), locUsed,deltaSumAvg))
                #update agend number
                x += 1 

        
    # find the not used transactions and give them a high weight (100 here) -> a high priorty to reduce them
    for l in range(0, len(transactions_attackert_knowlege)):
       
        transac= transactions_attackert_knowlege[l]    
        id = int(transac.attrib['id'])
        if id not in usedTrans:
            det = (transac.attrib['detector'])[6:-2]
            
            results.append(Trip("agent"+str(x),int(transac.attrib['time']),int(transac.attrib['time']),int(transac.attrib['time']), int(transac.attrib['cost']),set([det]),[id] ,100))
            usedTrans.add(id)
            x += 1
    #sort results. worst deltaSum first     
    results.sort(key = lambda c: c.deltaSum, reverse=True)
    


 



#compares trips and combines them if they are mostly equal. sum < min (walletcosts). if a trip has the sum of the min sum try to fill the next 
def compareTripsMin():
    #first limit, percentage should be higher as minlim to combine them in the first iteration
    minlim=40 
    #how often we iterated with minlim 0    
    zero = 0
    #tqdm manual    
    pbar = tqdm(total=len(results), desc="Generate Wallets")
    #sort wallets
    walletCosts.sort()
    #index
    pos = 0
     
    while(len(results) != len(walletCosts)):
        
        results.sort(key = lambda c: c.cost)
        tripA = ""
        tripB = ""
        #find for each trip the best trip with the best similarity
        for i, trip in enumerate(results):
            
            listA = trip.trip
            x=0
            v = 0
            for j  in range(v,len(results)):
                trip2=results[j]
                v = j
                if i != j:    
                    #split the trip string into a set
                    listB = trip2.trip
                    #create a list backwards
                    backwardsListB = backwards(listB)
                    #caluclate the similarity between the 2 trips, with Jaccard index
                    k = len(listA & listB) / float(len(listA|listB)) * 100
                    kBack = len(listA &  backwardsListB) / float(len(listA | backwardsListB)) * 100
                    #remeber the better trip
                    if (x < k or x < kBack) and (trip.cost+trip2.cost <= walletCosts[pos] or (zero > 0 and trip == results[0])):
                        tripA = trip
                        tripB = trip2
                        x = max(k,kBack)
            #only copy the best trip         
            if x > minlim:

                if len(results) == len(walletCosts):
                    break

                if tripA.cost+tripB.cost == walletCosts[pos]:
                        pos = pos+1
                
                copyTrip(tripA,tripB) 
                pbar.update(1)
               
        if len(results) == len(walletCosts):
                    break  
        #reduce the limit 
        minlim = max(minlim-20,0)
        
        if minlim == 0:
            zero += 1
            if zero > 3:
                
                break   
    zero = 0        
    pbar.close()


#compares trips and combines them if they are mostly equal. sum < max(walletcosts)
def compareTripsMax():
    #first limit, percentage should be higher as minlim to combine them in the first iteration
    minlim=60
    #how often we iterated with minlim 0    
    zero = 0    
    pbar = tqdm(total=len(results))
    while(len(results) != len(walletCosts)):
        x = 0
        results.sort(key = lambda c: c.cost)
        tripA = ""
        tripB = ""

        for trip in results:
           
            listA = trip.trip
            x=0
            for trip2 in results:
                
                if trip != trip2:    
                    
                    listB = trip2.trip
                    backwardsListB = backwards(listB)
                    k = len(listA & listB) / float(len(listA|listB)) * 100
                    kBack = len(listA &  backwardsListB) / float(len(listA | backwardsListB)) * 100
                    if (x < k or x < kBack) and (trip.cost+trip2.cost <= max(walletCosts) or (zero > 0 and trip == results[0])):
                        tripA = trip
                        tripB = trip2
                        x = max(k,kBack)
                        
            if x > minlim:
                if len(results) == len(walletCosts):
                    break
                copyTrip(tripA,tripB) 
                pbar.update(1)
                #print(x)
        minlim = max(minlim-20,0)
        if len(results) == len(walletCosts):
                    break  
        if minlim == 0:
            zero += 1
            if zero > 3:
                
                break   
    zero = 0        
    pbar.close()


#compares the trips and trys to add them up to reach the wallet sums
def compareTripsSum():
    
    #tqdm manual    
    pbar = tqdm(total=len(results))
    #sort wallets, try to fill the wallets with the lowest cost first
    walletCosts.sort()
      
        
    for k, wallet in enumerate(walletCosts):

        results.sort(key = lambda c: c.cost,reverse=True)        
        
        trip = results[k]

        x = k+1
        #combine them
        while trip.cost != wallet and  x < len(results)-1 and len(results) > len(walletCosts):
             
            for j in range(k+1,len(results)):
                trip2 = results[j]
                x=j
                if trip != trip2:    
                    
                    #save the better trip
                    if trip.cost+trip2.cost <= wallet :
                        copyTrip(trip,trip2) 
                        pbar.update(1)
                        break
          
    pbar.close()

#returns an array backwards
def backwards(array):

    n=4 #length of the edge name
    newarray=[]
    #cut edges in half and then combine them in backwards order
    for i in array:
        string1 = i[0:n//2] 
        string2 = i[n//2:]
        
        s = string2+string1
        newarray=  [s] + newarray
    return set(newarray)    

#combines two trips and removes one of them
def copyTrip(tripA,tripB):   
    
    tripA.cost += tripB.cost
    tripA.trip = tripA.trip.union(tripB.trip)
    tripA.deltaSum = (tripA.deltaSum + tripB.deltaSum)/2    
    tripA.used += tripB.used
    results.remove(tripB)


#gives the sum of all deviation values
def delta():
    d = 0
    for trip in results:
        d +=trip.deltaSum        
    return d

#removes the worst trips from the usedTrans list, so that they can be reused
#only the best i/n trips will remain
def analyseTrips2(i, n):
    results.sort(key = lambda c: c.deltaSum)    
    leng = len(results)
    x = int(leng*(i/n))
    for i, trip in enumerate(results):
        if x < i:
            for used in trip.used:
                usedTrans.remove(used)
                
    del[results[x+1:]]            

#generates a new trip 
def randomTrip():
    global results,usedTrans
    results = []
    usedTrans = set([])  
    findTrips() 
    
    
    
    
#uses the best results with the lowest difference and trys to optimise the routes with simulated annealing
def simAn():
    global results,usedTrans,annealingResult
    
    #iterations for simulated annealing
    n = annealing
    findTrips()
    d = delta()  
    for i in tqdm(range(0,n), desc="Find Plausible Trips"):
        
        rC = copy(results)
        uTC = usedTrans.copy()        
        d = delta()    
        
        #if(i%10 == 0):
            #print (i, d)

        #only use i/n of the trips and calculate the rest again. remove the other transactions from usedTrans list
        analyseTrips2(i, n) 
         
        #calc. new results and stroe them temp.
        findTrips()
        newResult = copy(results)
        newUsedTrans = usedTrans.copy()  
        newD = delta()
        #calc. completly new resuls
        randomTrip()
        randomD = delta()
        
        if(d < newD and d < randomD):
                #if the old results were better, restore them
                usedTrans = uTC.copy() 
                results = copy(rC)
        else:
            if(newD < randomD):
                #if the results with only i/n of the trips is better load them
                d = newD
                usedTrans = copy(newUsedTrans) 
                results = newResult.copy()  

            else:
                #else use the random results
                d=randomD
    annealingResult = d


            

#creates a list with all wallet costs and a list with all result costs
def create_list():
    global walletCosts,resultCosts
    walletCosts = []
    resultCosts=[]
    for i in root_attacker_knowlege.iter('wallet'):
        walletCosts.append(int(i.attrib['total_wallet_cost']))

    for result in results:   
        resultCosts.append(result.cost)
    


# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('-p', '--path', dest='rsc_path', type=str, help='Relative path to resource files', default='../rsc/')    
    parser.add_argument('-k', '--knowledge', dest='input_file_name', type=str, help='Specify attacker knowledge to be used for attack', required=True)
    parser.add_argument('-o', '--output', dest='output_file_name', type=str, help='Set output xml file name', default='attacker_advanced.xml')
    parser.add_argument('-r', '--report', dest='report_name', type=str, help='Set report name', default='report.txt')
    parser.add_argument('-t', '--simulatedTimes', dest='simulated_times_input_file_name', type=str, help='Specify knowlege for the attacker with traveltimes', default='simulated-times.xml')
    parser.add_argument('-n', '--simulatedAnnealing', dest='simulatedAnnealing', type=int, help='Number of interations', default='2')
    return parser.parse_args()

# Write report file
def report():
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(rsc_path + 'reports/' + rep_name, 'a+') as f:
        f.write('-------------------- Report of ADVANCED ATTACK --------------------\n\n')
        f.write('Name of attack script:   ' + sys.argv[0] + '\n')
        f.write('Attack started at        ' + str(rep_start) +'\n')
        f.write('Attack ended at          ' + str(rep_end) +'\n')
        f.write('Runtime:                 ' + str(time1 - time0) + '\n\n')
        f.write('simulated annealing iterations: ' + str(annealing) +'\n')
        f.write('simulated annealing result: ' + str(annealingResult) +'\n')
        f.write('Attacker knowledge file is   ' + "'" + rsc_path + 'knowledge/' + input_file_name + "'\n")
        f.write('- of file size               ' + str(os.path.getsize(rsc_path + 'knowledge/' + input_file_name)) + ' bytes\n\n')
        f.write('Output file is   ' + "'" + rsc_path + 'attacks/' + output_file_name + "'\n")
        f.write('- of file size   ' + str(os.path.getsize(rsc_path + 'attacks/' + output_file_name)) + ' bytes\n\n')
       
        f.write('-------------------- END of report --------------------\n\n')
    
    print('Report written to ' + "'" + rsc_path + 'reports/' + rep_name + "'")



def main():
    global DG,results,usedTrans,tree_attacker_knowlege,root_attacker_knowlege
    global transactions_attackert_knowlege
      #create new networkx graph
    DG = nx.DiGraph()

    #list with found trips
    results=[] 

    #set with the used trip ids
    usedTrans = set([])


    tree_attacker_knowlege = ET.parse(rsc_path + 'knowledge/' + input_file_name)
    
    root_attacker_knowlege = tree_attacker_knowlege.getroot()

    
    transactions_attackert_knowlege = root_attacker_knowlege[0]

    output_root = ET.Element('attack')

    

    print("Start Attacker")
    #generate the graph with the detector nodes
    generateGraph()  
    #find trips
    simAn()   
    #write trip results   
    trips =  ET.SubElement(output_root, "trips")
    for trip in results:
        strList = list(map(str, trip.used))
        ET.SubElement(trips, "trip", ids = " ".join(strList))

    create_list()
    compareTripsMin()
    compareTripsSum()
    compareTripsMax()
    #write wallet results
    wallets =  ET.SubElement(output_root, "wallets")
    for wallet in results:
        strList = list(map(str, wallet.used))
        ET.SubElement(wallets, "wallet",  ids = " ".join(strList) )
    tree = ET.ElementTree(output_root)
    tree.write(rsc_path + 'attacks/' + output_file_name)
    

    
   
    print('Finished')





if __name__ == '__main__':

    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    rsc_path = args.rsc_path
    input_file_name = args.input_file_name
    annealing = args.simulatedAnnealing
    simulated_times_file = args.simulated_times_input_file_name
    output_file_name = args.output_file_name
    rep_name = args.report_name
    

    # Global report variables
    rep_transactions = 0
    rep_vehicles = 0
    failed_assignments = 0
    remaining_transactions = 0
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    

    resultsWallets = []
    resultsTrips = []
    
    main()    
    report()

