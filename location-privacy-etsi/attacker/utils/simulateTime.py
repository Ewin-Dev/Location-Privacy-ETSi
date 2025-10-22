import xml.etree.ElementTree as ET
from lxml import etree
from statistics import mean
from lxml import etree
import os
import yaml




##########
# Run demand generation
# Takes inputs from rsc/traffic
# Writes outputs to rsc/traffic
##########

def generate(agents, parttime, nighttime, days):
    # Compose command 'exe' and execute it
    exe = 'cd ' + '../../agent' + '&& python ' + 'agent_generation.py'
    #exe += ' --inpath ' + '../attacker/utils/'                  # default inpath is rsc/traffic
    # exe += ' --outpath ' + '../attacker/utils/'
    exe += ' --agents ' + str(generation.get('agents'))
    exe += ' --parttime ' + str(generation.get('parttime'))
    exe += ' --nighttime ' + str(generation.get('nighttime'))
    exe += ' --days ' + str(days)
    exe += ' --mapin ' + str(generation.get('mapin'))
    exe += ' --routesout ' + str(generation.get('groutesout'))
    exe += ' --vehmapout ' + str(generation.get('gvehmapout'))
    exe += ' --homedistrict ' + str(generation.get('homedistrict'))
    exe += ' --workdistrict ' + str(generation.get('workdistrict'))
    exe += ' --no-report '
    os.system(exe)




##########
# Run the simulation
# Uses the input files in rsc/traffic by default, different input directory can be set by --inpath
# Outputs challenger.xml to attacker/utils directory
##########

def simulate(challengerXMLname):
    # Compose command 'exe' and execute it
    exe = 'cd ' + '../../simulation' + '&& python ' + 'simulation.py'
    #exe += ' --inpath ' + '../attacker/utils/'                  # default inpath is rsc/traffic
    exe += ' --outpath ' + '../attacker/utils/'
    exe += ' --sumocfg ' + simulation.get('sumocfg')
    exe += ' --detectors ' + simulation.get('detectors')
    exe += ' --cout ' + challengerXMLname
    exe += ' --aout ' + simulation.get('aoutput')
    exe += ' --junctions ' + simulation.get('junctions')
    exe += ' --tripinfo ' + simulation.get('tripinfo')
    exe += ' --no-report '
    os.system(exe)

    # Delete attacker.xml afterwards since this is not needed
    os.remove('attacker.xml')



##########
# edgeClass is used to store times for each edge
##########

class edgeClass:
  def __init__(self, fromDetector, toDetector, time):
    self.time = []
    self.fromDetector = fromDetector
    self.toDetector = toDetector
    self.time.append(time) #adds the time when creating an new object

# Store every edge (edgeClass object)
edges = []

##########
# Iterates through the edges of challengerXMLname
# For each edge found in a trip, either create a new edge Object or -- if already existing -- append required time to this object
# Thus, can be executed multiple times in succession to add further travel times
# After executing, the array 'edges' contains all edges found in the trips with all travel times
##########

def generateTimes(challengerXMLname):
    tree = ET.parse(challengerXMLname)
    root = tree.getroot()

    # Iterate over all trips
    for elemTrip in root.iter('trip'):
        first = True
        # For each transaction, save the time difference between two detectors
        for elem in elemTrip.iter('trip_transaction'):
                
            time = int(elem.attrib['time'])
            fromDetector = elem.attrib['detector']

            # Create the start point for the first entry in the current trip
            if first:
                oldtime = time
                oldfromDetector = fromDetector
                first = False

            else:
                # Get time difference
                t = time - oldtime
                
                # Check if the detector / edge is known
                edgeFound = False
                for obj in edges:
                    # If the edge was used before add the time difference to the time array of this edge
                    if obj.fromDetector == oldfromDetector and obj.toDetector == fromDetector:
                        # Add time to edge
                        obj.time.append(t)
                        edgeFound = True
                        break
                # Create new edge between two detectors if edge was not in the edges array
                if not edgeFound:
                    edges.append(edgeClass(oldfromDetector,fromDetector,t))

                # New times become the old times
                oldtime = time
                oldfromDetector = fromDetector

##########
# Creates a file with travel times from one detector to another detector (ignoring routes where a detector is between start detector and end detector)
##########

def createTimeFile(outputXMLname):
    
    routes = etree.Element('routes')
    
    for edge in edges:
        etree.SubElement(routes, 'route', fromDetector=edge.fromDetector ,toDetector=edge.toDetector, minTime=str(min(edge.time)), maxTime=str(max(edge.time)), avg = str(round(mean(edge.time))))
                        
    mydata = etree.ElementTree(routes)
    mydata.write(outputXMLname, pretty_print=True)


#######################################################################


def main():
    # Run multiple simulations to create simulated-times file
    # X in range(X) is the number of simulations
    # generate(agents, part-time worker percentage, number of days) runs the agent-generation
    # simulate runs the i-th simulation and creates a temporary output challengeri.xml
    # generateTimes updates times based on the challengeri.xml file

    for i in range(10):
        generate(200, 5, 5, 2)
        simulate('challenger' + str(i) + '.xml')
        generateTimes('challenger' + str(i) + '.xml')
        # Delete challengeri.xml when it is not needed any longer
        os.remove('challenger' + str(i) + '.xml')

    # Write travel times of each edge to an XML file in the rsc/knowledge folder
    createTimeFile('../../rsc/knowledge/simulated-times.xml')

if __name__ == '__main__':
    config = yaml.load(open('../../rsc/config/config.yaml'), Loader=yaml.FullLoader)
    generation = config.get('generation')
    simulation = config.get('simulation')
    main()
