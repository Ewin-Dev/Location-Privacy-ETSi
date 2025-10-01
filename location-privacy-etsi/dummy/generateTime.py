import xml.etree.ElementTree as ET
from lxml import etree
from subprocess import run
from shlex import split
from lxml import etree
import os

detector_edges = []

#list with all edges where a detecor is placed
def fill_detector_edges_list():
    
    tree_detectors = ET.parse('dummy-detectors.add.xml')
    root_detectors = tree_detectors.getroot()
    for detector in root_detectors.iter('e1Detector'):
        lane = detector.attrib['lane']        
        edge = lane.find("_")
        edge = lane[:edge]
        if not edge in detector_edges:
            detector_edges.append(edge)


#creates routes from every edge to all other detectors
def createRoutes():
    routes = etree.Element('routes')
    tree = ET.parse('dummy-detectors.add.xml')
    root = tree.getroot()
    ids = 0                         #id for routes and vehicles  

    for detector_edge in detector_edges:      

        for toDetector in root.iter('e1Detector'):
                #get just the edge
                lane2 = toDetector.attrib['lane']
                edge2 = lane2.find("_")

                #ignore routes from one detector to the detector on the same edge
                if detector_edge != toDetector.attrib['lane'][:-2]:
                    arrivalLane = lane2[-1:]
                    edge2 = lane2[:edge2]  
                                
                    etree.SubElement(routes, 'route', id=str(ids) , edges=detector_edge + ' ' + edge2)
                    etree.SubElement(routes, 'vehicle', id=str(ids) , route=str(ids) , depart='0' , arrivalLane = arrivalLane)
                    ids = ids +1 

    mydata = etree.ElementTree(routes)
    mydata.write('attacker-routes.xml', pretty_print=True)  

#creates a file with min traveltime from one detector to another detector (ignoring routes where a detector is between start detector and end detector)
def createTimeFile():
    tree = ET.parse('attacker.rou.alt.xml')
    root = tree.getroot()
    tree_grid = ET.parse('dummy-grid.net.xml')
    root_grid = tree_grid.getroot()
    routes = etree.Element('routes')

    
    
    for elemVeh in root.iter('vehicle'):
        
        elem = elemVeh[0]
        #use only the routes with the right edges     
        if (len(elem) > 1):
            edges_route = elem[1].attrib['edges']
            elem.remove(elem[0])
        else:
            edges_route = elem[0].attrib['edges']            

        edge_lenth = edges_route.find(" ")
        edges_route_reduced = edges_route[edge_lenth+1:-edge_lenth-1]
        index = len(detector_edges)-1

        for detector in detector_edges:
            if detector in edges_route_reduced:         
                elem.remove(elem[0])
                break 
            #if there was no detecor between the start and end detector use this route        
            if  detector == detector_edges[index]:
                #remove the first exit time, because detectors are at the and of an edge
                time = float(elem[0].attrib['cost']) - float(elem[0].attrib['exitTimes'][:3])
                fromEdge=edges_route[:edge_lenth]

                #checking lane conection
                for edge in root_grid.iter('connection'):
                    
                    if edge.attrib['from'] == fromEdge and edge.attrib['to'] == edges_route[edge_lenth+1:edge_lenth+edge_lenth+1]:
                        
                        etree.SubElement(routes, 'route', fromDetector='e1det_'+fromEdge+'_'+edge.attrib['fromLane'] ,toDetector='e1det_'+edges_route[-edge_lenth:]+'_'+elemVeh.attrib['arrivalLane'], time=str(round(time,2)), edges = edges_route)        
                        
    mydata = etree.ElementTree(routes)
    mydata.write('attacker-detectors-time.xml', pretty_print=True)  

#using sumo duarouter to get the fastest routes
def findRoutes():
    completed_process = run(split('duarouter --route-files attacker-routes.xml --net-file dummy-grid-tls.net.xml --output-file attacker.rou.xml --exit-times True --ignore-errors'))
    if completed_process.returncode != 0:
        raise Exception( f'Invalid result: { completed_process.returncode }' )
    print(completed_process)

def main():
    fill_detector_edges_list()
    createRoutes()
    findRoutes()
    createTimeFile()
    if os.path.exists("attacker.rou.alt.xml") & os.path.exists("attacker.rou.xml"):
        os.remove("attacker.rou.alt.xml")
        os.remove("attacker.rou.xml")
    else:
        print("The file does not exist")

    if os.path.exists("attacker-routes.xml"):
        os.remove("attacker-routes.xml")
    else:
        print("The file does not exist")    
    print('Finished')

if __name__ == '__main__':
    main()    
