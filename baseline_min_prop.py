import pandas as pd
from yafs.core import Sim
from yafs.application import Application, Message
from yafs.population import *
from yafs.selection import Selection
from yafs.topology import Topology
from simpleSelection import CustomPath
from simplePlacement import CloudPlacement
from yafs.stats import Stats
from yafs.distribution import deterministicDistribution
from yafs.utils import fractional_selectivity
import time
import operator
import numpy as np
import sys
is_first = True
sys.dont_write_bytecode = True

base_line_data = pd.DataFrame(columns=["state","Edge Device", "Latency"])
state_edge_device_mapper = dict()

def reward(obs_latency,src,dest):

    # print("observed latency = ", obs_latency)
    global is_first
    # print("source: ",src)
    # print("dest: ",dest - smallest_node)
    # print("latency: ",obs_latency)
    if is_first:
        # print("get reward called")
        destination = (dest - smallest_node)
        if str(edges_state) not in state_edge_device_mapper.keys():
            state_edge_device_mapper[str(edges_state)] = dict()
        
        if destination in state_edge_device_mapper[str(edges_state)].keys():
            temp_latency = state_edge_device_mapper[str(edges_state)][destination]
            state_edge_device_mapper[str(edges_state)][destination] = min(temp_latency,obs_latency)

        is_first = False
        state_edge_device_mapper[str(edges_state)][destination] = obs_latency
    # print("successfully calculated the latency")

def get_action(s_node,state):
    global smallest_node
    global is_first
    smallest_node = s_node
    global edges_state
    edges_state = state

    propogation_delay = edges_state["PR"]
    propogation_delay_sorted = sorted(propogation_delay.items(), key=operator.itemgetter(1))
    # print("action chosen successfully")
    list_edge_devices = list()
    for i in range(8):
        list_edge_devices.append(propogation_delay_sorted[i][0])
    
    is_first = True
    return list_edge_devices


# @profile
def main(get_action,reward,add_time, iteration, simulated_time):

    # random.seed(RANDOM_SEED)
    # np.random.seed(RANDOM_SEED)

    """
    PLACEMENT algorithm
    """
    placement = CloudPlacement(
        "onCloud")  # it defines the deployed rules: module-device
    # apply the algo on service A
    placement.scaleService({"ServiceA": 2})

    """--
    SELECTOR algorithm
    """
    # Their "selector" is actually the shortest way, there is not type of orchestration algorithm.
    # This implementation is already created in selector.class,called: First_ShortestPath
    selectorPath = CustomPath(Selection,get_action,execution_type="baseline_min_prop")
    selectorPath.create_topology()
    selectorPath.set_population()

    """
    SIMULATION ENGINE
    """

    stop_time = simulated_time
    s = Sim(True,reward,selectorPath.topology, add_time,
            default_results_path="Results_" + str(iteration))
    s.deploy_app(selectorPath.app, placement, selectorPath.pop, selectorPath)
    selectorPath.init_state(s)
    s.run(stop_time, selectorPath, show_progress_monitor=False)



def driver(get_action,reward):
    start_time = time.time()

    add_time = 0

    for i in range(1):

        main(get_action,reward,add_time, i, simulated_time=230)

        add_time += 100

        m = Stats(defaultPath="Results_" + str(i))  # Same name of the results
        time_loops = [["M.A", "M.B"]]


if __name__ == '__main__':

    for i in range(12000):
        print("episode running {}/{}".format(i+1,12000))
        driver(get_action,reward)

    for sedm in state_edge_device_mapper.keys():

        edge_data = state_edge_device_mapper[str(sedm)]
        base_line_data = base_line_data.append({
            "state": str(sedm),
            "Edge_Device": int(edge_data.keys()[0]),
            "Latency": edge_data[edge_data.keys()[0]]
        },ignore_index=True)

base_line_data.to_csv("baseline_min_prop_8.csv",index=False)