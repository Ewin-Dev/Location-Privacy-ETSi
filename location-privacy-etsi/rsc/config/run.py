import os
from time import time
import yaml


# This script runs the whole simulation, attack and evaluation based on the file 'config.yaml'
# It consists of three methods simulate(), attack() and evaluate(), each of which composes a command 'exe' based on the config file and runs this command afterwards
# A report is written to the folder 'reports', the file name is specified in the config file
# The actual methods report writing must be part of the individual attack and evaluation scripts


def generate():
    print('\n-- Generation module --')

    # Compose command 'exe' and execute it
    exe = 'cd ' + generation.get('path') + '&& python ' + generation.get('script')
    exe += ' --inpath ' + str(generation.get('inpath'))
    exe += ' --outpath ' + str(generation.get('outpath'))
    exe += ' --agents ' + str(generation.get('agents'))
    exe += ' --parttime ' + str(generation.get('parttime'))
    exe += ' --nighttime ' + str(generation.get('nighttime'))
    exe += ' --days ' + str(generation.get('days'))
    exe += ' --mapin ' + str(generation.get('mapin'))
    exe += ' --routesout ' + str(generation.get('groutesout'))
    exe += ' --vehmapout ' + str(generation.get('gvehmapout'))
    exe += ' --homedistrict ' + str(generation.get('homedistrict'))
    exe += ' --workdistrict ' + str(generation.get('workdistrict'))
    if not generation.get('report'):
        exe += ' --no-report '
    exe += ' --reportpath ' + str(generation.get('reportpath'))
    exe += ' --reportname ' + str(generation.get('reportname'))
    os.system(exe)



def simulate():
    print('\n-- Simulation module --')

    # Compose command 'exe' and execute it
    exe = 'cd ' + simulation.get('path') + '&& python ' + simulation.get('simulator')
    exe += ' --inpath ' + str(simulation.get('inpath'))
    exe += ' --outpath ' + str(simulation.get('outpath'))
    if simulation.get('gui'):
        exe += ' --gui'
    exe += ' --sumocfg ' + simulation.get('sumocfg')
    exe += ' --cout ' + simulation.get('coutput')
    exe += ' --aout ' + simulation.get('aoutput')
    exe += ' --junctions ' + simulation.get('junctions')
    exe += ' --detectors ' + simulation.get('detectors')
    exe += ' --tripinfo ' + simulation.get('tripinfo')
    exe += ' --seed ' + str(simulation.get('seed'))
    if not simulation.get('report'):
        exe += ' --no-report '
    exe += ' --reportpath ' + str(simulation.get('reportpath'))
    exe += ' --reportname ' + str(simulation.get('reportname'))
    os.system(exe)



def attack():
    print('\n-- Attacker module --')

    # Compose command 'exe' and execute it
    exe = 'cd ' + attacker.get('path') + '&& python ' + attacker.get('attack')
    exe += ' --knowledge ' + attacker.get('input')
    exe += ' --output ' + attacker.get('output')
    exe += ' --report ' + report
    os.system(exe)

def attackerAdvanced():
    print('\n-- Attacker Advanced module --')

    # Compose command 'exe' and execute it
    exe = 'cd ' + attackerAdvanc.get('path') + '&& python ' + attackerAdvanc.get('attack')
    exe += ' --knowledge ' + attackerAdvanc.get('input')
    exe += ' --output ' + attackerAdvanc.get('output')
    exe += ' --report ' + report
    exe += ' --simulatedAnnealing ' + str(attackerAdvanc.get('simulatedAnnealing'))
    exe += ' --simulatedTimes ' + str(attackerAdvanc.get('simulatedTimes'))
    os.system(exe)    



def evaluate():
    print('\n-- Evaluation module --')

    # Compose command 'exe' and execute it
    exe = 'cd ' + eval.get('path') + '&& python ' + eval.get('evaluator')
    exe += ' --challenger ' + eval.get('challenger')
    exe += ' --attacker ' + eval.get('attacker')
    exe += ' --report ' + report
    os.system(exe)



if __name__ == "__main__":
    # Load yaml config file
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)

    # Empty report file
    report = config.get('report')
    f = open('../reports/' + report, 'w')

    # Get outer tags 'simulation', 'attacker' and 'evaluation' from config file
    generation = config.get('generation')
    simulation = config.get('simulation')
    attacker = config.get('attacker')
    attackerAdvanc = config.get('attackerAdvanced')
    eval = config.get('evaluation')

    # If parameter 'run' is True, run the corresponding step
    if generation.get('run'):
        generate()

    if simulation.get('run'):
        simulate()

    if attacker.get('run'):
        attack()

    if attackerAdvanc.get('run'):
        attackerAdvanced()    

    if eval.get('run'):
        evaluate()
    
    if simulation.get('run'):
        newname = generation.get('net_prefix') + '_' + str(generation.get('agents')) + '_' + str(generation.get('days')) + '_' + simulation.get('coutput')
        os.replace('../' + simulation.get('outpath') + simulation.get('coutput'), '../' + simulation.get('outpath') + newname)
        newname = generation.get('net_prefix') + '_' + str(generation.get('agents')) + '_' + str(generation.get('days')) + '_' + simulation.get('aoutput')
        os.replace('../' + simulation.get('outpath') + simulation.get('aoutput'), '../' + simulation.get('outpath') + newname)
