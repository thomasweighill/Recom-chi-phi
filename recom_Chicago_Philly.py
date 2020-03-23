from gerrychain import Graph, Election, updaters, Partition, constraints, MarkovChain
from gerrychain.updaters import cut_edges
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part
from gerrychain.accept import always_accept
import numpy as np
from functools import partial
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import math
import pickle
import sys, os
import networkx as nx
from itertools import product
import littlehelpers

'''
User entered parameters for the run
'''
steps = int(sys.argv[1]) #recom steps
INTERVAL = int(sys.argv[2]) #sampling interval
outputfolder = sys.argv[3] #outputfolder
num_districts = int(sys.argv[4])
city = sys.argv[5]
os.makedirs(outputfolder, exist_ok=True)
print("Arguments: ", sys.argv[1:])

'''
State and district level parameters
'''
pop_tol = 0.02
pop_col = "TOTPOP"

if city == "Chicago":
    print("Loading Chicago...")
    graph = Graph.from_file("Chicago_Precincts/Chicago_Precincts.shp")
elif city == "Phillyblocks":
    print("Loading Philly blocks...")
    graph = Graph.from_file("Philly_blocks/Philly_blocks_with_dems.shp")
else:
    print("Loading Philly..")
    graph = Graph.from_file("Philly_Divisions/Philly_divisions_with_demos.shp")

total_population = sum([graph.nodes[n][pop_col] for n in graph.nodes()])

print("Shapefiles loaded and ready to run ReCom...")

'''
Run the chain
'''
for k in [num_districts]:
    HISPs = []
    POPs = []
    BPOPs = []
    pop_target = total_population/k
    myproposal = partial(recom, pop_col=pop_col, pop_target=pop_target, epsilon=pop_tol/k, node_repeats=2)
    #updaters
    myupdaters = {
        "population": updaters.Tally(pop_col, alias="population"),
        "HISP": updaters.Tally("HISP", alias="HISP"),
        "BPOP": updaters.Tally("NH_BLACK", alias="BPOP")
    }

    #initial partition
    initial_ass = littlehelpers.factor_seed(graph, k, pop_tol, pop_col)
    initial_partition = Partition(graph, initial_ass, myupdaters)

    #chain
    compactness_bound = constraints.UpperBound(
        lambda p: len(p["cut_edges"]),
        2*len(initial_partition["cut_edges"])
    )
    myconstraints = [
        constraints.within_percent_of_ideal_population(initial_partition, pop_tol),
        compactness_bound
    ]
    chain = MarkovChain(
        proposal=myproposal,
        constraints=myconstraints,
        accept=always_accept,
        initial_state=initial_partition,
        total_steps=steps
    )

    #run ReCom
    for index, step in enumerate(chain):
        if index%INTERVAL == 0:
            print(index, end=" ")
            HISPs.append(list(step["HISP"].values()))
            POPs.append(list(step["population"].values()))
            BPOPs.append(list(step["BPOP"].values()))

pickle.dump((HISPs, BPOPs, POPs), open(outputfolder+"/run_data.p", "wb"))
