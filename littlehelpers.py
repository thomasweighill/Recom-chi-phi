import operator
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
from gerrychain import Graph, Partition, updaters
from gerrychain.tree import recursive_tree_part

def relabel_by_dem_vote_share(part, election):
    '''
    Renumbers districts by DEM vote share, 0-indexed
    '''
    dem_percent = election.percents('Democratic')
    unranked_to_ranked = sorted([(list(part.parts.keys())[x], dem_percent[x])
                                  for x in range(0, len(part))],
                                  key=operator.itemgetter(1))
    unranked_to_ranked_list = [x[0] for x in unranked_to_ranked]
    unranked_to_ranked = {unranked_to_ranked[x][0]:x for x in range(0, len(part))}
    newpart = Partition(part.graph, {x:unranked_to_ranked[part.assignment[x]] for x in part.graph.nodes}, part.updaters)
    return newpart

def plot_districts_and_labels(part, gdf, labels, cmap="tab20c"):
    '''
    Plots districts with labels on them

    :param part: a partition
    :param gdf: a geodataframe matching part
    :param labels: a dictionary matching districts to strings
    '''
    gdf["assignment"] = [part.assignment[x] for x in part.graph.nodes]
    districts = gdf.dissolve(by="assignment")
    centroids = districts.geometry.representative_point()
    districts["centroid"] = centroids
    fig, ax = plt.subplots(figsize=(20,20))
    part.plot(gdf, cmap=cmap, ax=ax)
    districts.boundary.plot(ax=ax, edgecolor='black')
    for idx, row in districts.iterrows():
        ax.annotate(s=str(labels[row.name]), xy=row['centroid'].coords[0],
                 horizontalalignment='center')
    plt.show()
    del gdf["assignment"]

def split_districts(part, factor, pop_target, pop_col, pop_tol):
    '''
    Takes a districting plan and splits each district into smaller ones
    '''
    #must be 0-indexed!
    ass = {}
    graph = part.graph
    for d in part.parts:
        subgraph = graph.subgraph(part.parts[d])
        subdistricts = recursive_tree_part(subgraph, range(factor), pop_target, pop_col, pop_tol)
        for x in subgraph.nodes:
            ass[x] = d*factor+subdistricts[x]
    return ass

def factor_seed(graph, k, pop_tol, pop_col):
    '''
    Recursively partitions a graph into k districts.

    Returns an assignment.
    '''
    total_population = sum([graph.nodes[n][pop_col] for n in graph.nodes])
    pop_target = total_population/k
    num_d = 1
    ass = {x:0 for x in graph.nodes}
    while num_d != k:
        for r in range(2, int(k/num_d)+1):
            if int(k/num_d) % r == 0:
                print("Splitting from {:d} down to {:d}".format(
                        int(num_d),
                        int(r*num_d)
                        )
                     )
                ass = split_districts(
                    Partition(graph, ass),
                    r,
                    pop_target*k/num_d/r,
                    pop_col,
                    pop_tol/k
                )
                num_d *= r
                break
    return ass
