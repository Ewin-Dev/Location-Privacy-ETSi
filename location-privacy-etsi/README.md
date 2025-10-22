# ETSi – A Simulation Framework for Location Leakage in Electronic Toll Collection

This README is supposed to give **technical** information about this framework and explain how it should be used. For a more theoretical approach and the results that this framework (or more specificly the implemented attack) achieves please refer to the paper.pdf in the documentation folder of this project.

## Structure of this Project

This project is generally divided into four different modules:
- Agent/Demand Generation
- Traffic Simulation & data generation
- Attack
- Evaluation

Each module can be run without needing any of the other ones, but it is recommended to use the build-in pipeline to ensure that everything works smoothly.

## Agent/Demand Generation

The Agent Generation can be found in the *agent* folder. It uses different kinds of agents and districts to generate routes, which can then be used by the simulation.

Currently implemented agent types include:
* **Basic worker**:
The basic agents use given home- and workdistricts to randomly generate a home- and a workaddresses between which they then daily commute.
* **Parttime worker**:
The parttime workers work similiar to the basic agents, but they only work half the week and on the other days they do a number (1-5) different chores all throughout the day.
* **Nighttime worker**:
The nighttime workers are basicly the basic agents but they work at night times, so that the simulation does not have as much downtime and can handle more agents all in all.

### Output

Using the agent generation will create a *routes.xml* file which contains details of every route which every agent in the simulation will then use.
Also it creates a *vehicle_map.csv* which is used to map every trip to a specific agent, because SUMO itself does not track a car after its route is done.

## Traffic Simulation & Data Generation

In this module, which can found in the *simulation folder* the output from the agent generation is used to generate knowledge of the challenger and a subset of that as knowledge from the attacker. While it sounds straightforward there are a few different steps that are being taken.

### Generating Junctions and Junction Costs

Because SUMO works just the way it does, in a first step all detectors from the *detectors.add.xml* file are used (assuming the file was created by the [generateTLSE1Detectors script](https://sumo.dlr.de/docs/Tools/Output.html#generatetlse1detectorspy) to generate a *junctions.xml* which contains every junction with every detector that is on that junction and a corresponding cost.

### Running the simulation

Next the full simulation will run.
Inside the simulation on every single timestep it is checked if any detector found a vehicle and if so, a transaction, which contains the vehicle (agent), the trip, the detector and the timestep at which it took place.

### Detecting and removing "bad" entries

We have found that very often a detector will detect a vehicle at timestep $`x`$ and additionally at timestep $`x+1`$ or even $`x+2`$ (this does, to our knowledge, not mean a vehicle that stops at a traffic light, because then, the detector would find it even more often).
Since we can only accept a vehicle once at any junction in a reasonable timeframe (remember, the real life background would be toll stations), we need to find those entries and remove them.
Sadly those "bad" entries are around 40% of the total transactions and their removement takes a lot of time if the number of transactions is high.

### Cross-referencing junctions with detector knowledge

Next, for every transaction we reference the given detector to the before generated junctions file to have the information at which junctions the transaction took place and what the costs were. That way we generate the total challenger knowledge. Then we take a subset of every transaction and use that as attacker knowledge, because the attacker does not know which vehicle did the transaction or on which trip the vehicle was.

### Output

Output from the simulation are a `challenger.xml` and an `attacker.xml` which are renamed later, but are used with those names in the complete pipeline.

## Attacker

The attacker module can be found in the *attacker folder*. The attacker needs a $.xml$ file with the attacker knowlage as input (in the pipeline the `attacker.xml` is used)

### Advanced Attacker

The advanced attacker uses the `attack_advanced.py` and tries to reconstruct trips with the `simulated-times.xml` and then combines them to wallets.

#### Find Plausible Trips

The advanced attacker tries to find plausible trips. A plausible trip is a list of transactions, if the detectors from the transactions are connected and reachable in a plausible time. The deviation from the average travel time will be saved for every trip. With simulated annealing the attacker trys to approximate a global optimum with the lowest sum of the deviations. Transactions that are not in a trip will recive a high weigh, so that there is a high priority to minimize them. 

#### Generate wallets

Trips that are similar will be combined and the attacker reduces the ammount to the ammount of wallets. In the process the attacker trys to get close to the wallet costs (like subset sum).

#### Output

The output file is a the `attack_advanced.xml` in  `rsc/attacks`. It contains the trips that were found before the walletes were generated. Every trip there contains the transaction IDs. Also the file contains the wallets, each wallet contains the transaction IDs as well.


## Evaluation

The evaluation module rates the attacker's success based on the challenger knowledge (output of simulation) and the attack result (output of attacker).
When using own attacker and evaluation scripts, one needs to assure that the structure of the XML files output by the simulation and attacker match the structure required by the evaluation.

The `evaluation_advanced.py` uses the *Jaccard index* to compare an attacker wallet $`A`$ (i.e., a wallet composed by the attacker) and a real true wallet $`C`$ by
```math
J(A,C) = \frac{\lvert A \cap C \rvert}{\lvert A \cup C \rvert} \in [0,1]
```
and calculates the attackers success as
```math
\frac{1}{\lvert \mathcal A \rvert} \sum_{A \in \mathcal A} \, \max_{C \in \mathcal C} \, J(A,C),
```
where $`\mathcal{A}`$ and $`\mathcal{C}`$ are the sets of attacker and challenger wallets.

## Running the project & Pipeline

The easiest way to run the project is to use `run.py` which can be found in the `rsc/config` folder.
This folder also contains the very important `config.yaml` in which every single configuration/moving variable that are used in this project can be altered.
In this file you can also choose which components should be executed by switch the `run` variable for every module between `True` and `False`.

### Important Agent Generation Configurations
* **agents**:
total number of agents to be used
* **days**:
total number of days to be simulated
* **parttime/nighttime**:
percentage of part/night time workers from the total number of workers
* **mapin**:
the network on which the simulation should take place
* **homedistrict/workdistrict**:
convex polygones that define the district. Polygones are in the format '"x1,y1 x2,y2 ..."' and the points need to be given counter-clockwise.

### Important Simulation Configurations
* **detectors**: gives the detector file which should be used for the simulation
* **sumocfg**: the SUMO-config file which should contain the same network, routes, and detectors as are in the config.yaml
* **gui**: wether the SUMO-GUI should be used for the simulation. We higly discourage you from using the GUI if you need to run fast simulations!

### Important attackerAdvanced Configurations
* **attack**: the name of the attack file that is used
* **simulatedTimes**: the name of the file with the traveltime information between detectors
* **simulatedAnnealing**: the number of iterations to approximate a global optimum of plausible trips
### Important Evaluation Configurations
* **evaluator**: the name of the evaluation file that is used

### How to run

Given you want to run run a complete simulation and attack you need to:
* Install the requirements of this projects by using `pip install -r requirements.txt`
* Have a map, which is created by sumo and give it a name ending with `.xml`, **without** the `.net`
* Create a detector file for the map with the [script from sumo](https://sumo.dlr.de/docs/Tools/Output.html#generatetlse1detectorspy)
* Create a *sumocfg* file which contains the map, the detectors and the routes
* Put all three files in the *rsc/traffic* folder
* Change the generation/mapin, simulation/detectors and simulation/sumocfg variables in the ***config.yaml*** to the names of your files
* Change the generation/homedistrict and generation/workdistrict according to your map
* ***Run the simulateTime.py file, which can be found in attacker/utils. This will take a lot of time, but is needed for the advanced attacker. This is corresponding to your attacker learning average times of most if not all the routes between detectors, which are used in the network***
* ***simulateTime.py will create a simulated-times.xml file. The .xml file is stored in `rsc/knowledge`. ***
* Execute the `run.py` file, which is found in the `rsc/config` folder
* The result will be in `rsc/reports/report.txt`

## Known problems

* The nightime workers are currently bugged and therefore should be set to 0% in the configuration
* You need to make sure that you have the rights to read, rename and write files in the location the project is in. Or, as a Windows user, run a admin shell to execute `python run.py`
