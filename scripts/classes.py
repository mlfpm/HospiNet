import numpy as np
import pickle
import operator
import networkx as nx
import copy


class HospiNode:
    """
    Created on Apr 25, 2020

    @author: GiuliaMuzio
    """

    def __init__(
        self,
        label,
        n_beds,
        n_init_patients,
        n_init_prev_count,
        max_distance,
        capacity_thresh,
    ):
        self.label = label  # label in the France_graph
        self.n_beds = n_beds  # dictionary - {‘icu’, ‘normal’}
        self.n_patients = copy.deepcopy(
            n_init_patients
        )  # the total after update and redistribution
        self.prev_count = copy.deepcopy(
            n_init_prev_count
        )  # raw number from the time series
        self.max_distance = copy.deepcopy(max_distance)
        self.capacity_thresh = copy.deepcopy(capacity_thresh)

    def over_capacity(self, which):
        # the number of patients that are over capacity by unit: "acute", "icu", this is what we would like to transfer
        return np.ceil(
            self.n_patients[which] - (self.capacity_thresh[which] * self.n_beds[which])
        )

    def availability(self, which):
        # the number of patients by unit: "acute", "icu" that we can accept without going over capacity
        if which == "all":  # perform the calculation on everything
            availability = self.total_beds - self.total_patients
        else:  # perform the calculation only for the chosen kind of bed: "acute", "icu"
            availability = (
                self.capacity_thresh[which] * self.n_beds[which]
            ) - self.n_patients[which]

        return np.floor(availability) if availability > 0 else 0

    def occupancy_percentage(self, which):
        # percentage of occupied beds, perform the calculation only for the chosen kind of bed
        return (
            (self.total_patients / self.total_beds) * 100.0
            if which == "all"
            else (self.n_patients[which] / self.n_beds[which]) * 100.0
        )

    def add_new_patients(self, curr_count):
        self.n_patients["icu"] += (
            (curr_count["icu"] - self.prev_count["icu"])
            if (curr_count["icu"] - self.prev_count["icu"]) >= 0
            else 0
        )
        self.n_patients["acute"] += (
            (curr_count["acute"] - self.prev_count["acute"])
            if (curr_count["acute"] - self.prev_count["acute"]) >= 0
            else 0
        )
        self.prev_count = curr_count
        return

    def add_incoming_patients(self, in_patients):
        self.n_patients["icu"] += in_patients["icu"]
        self.n_patients["acute"] += in_patients["acute"]
        return

    def remove_outgoing_patients(self, out_patients):
        self.n_patients["icu"] -= out_patients["icu"]
        self.n_patients["acute"] -= out_patients["acute"]
        return

    @property
    def total_beds(self):
        return self.n_beds["icu"] + self.n_beds["acute"]

    @property
    def total_patients(self):
        return self.n_patients["icu"] + self.n_patients["acute"]


class HospiGraph:
    """
    Created on Apr 25, 2020

    @author: semese
    """

    def __init__(self, hparams):
        self.degree_orders = None
        self.node_list = None
        self.distance_matrix = None
        self.hospi_nodes = None

        self.init_graph_details(hparams)

    def init_graph_details(self, hparams):
        # create a graph temporarily
        france_graph = self.load_and_build_graph(hparams)

        # compute parameters of interest
        self.degree_orders = self.sort_nodes_by_deg(france_graph)
        self.node_list = list(france_graph.nodes)
        self.distance_matrix = nx.floyd_warshall_numpy(france_graph, weight="distance")

        # generate the HospiNodes
        self.hospi_nodes = self.build_node_list(hparams)

        return

    @staticmethod
    def load_and_build_graph(hparams):
        # Load and build graph
        with open(hparams["graph_path"], "rb") as handle:
            france = pickle.load(handle)
        france_graph = nx.Graph(france)

        # Load distances and times
        with open(hparams["dist_path"], "rb") as handle:
            france_dist = pickle.load(handle)

        # Set distances as edge attributes - they are transformed to kms!
        nx.set_edge_attributes(
            france_graph,
            {
                (u, val["code"]): val["distance"] / 1000
                for u, value in france_dist.items()
                for val in value
            },
            "distance",
        )

        return france_graph

    @staticmethod
    def sort_nodes_by_deg(france_graph):
        # get a sorte list of (node_label, node_degree) pairs ordered ascending by degree
        degree_list = list(france_graph.degree)
        degree_list.sort(key=operator.itemgetter(1))
        return degree_list

    def build_node_list(self, hparams):
        # Read bed info from file
        with open(hparams["attr_path"], "rb") as handle:
            bed_info = pickle.load(handle)

        # Create a custom node dictionary
        node_dict = {}
        for i, node_lab in enumerate(self.node_list):
            new_node = HospiNode(
                node_lab,
                bed_info[node_lab]["beds"],
                hparams["init_n_patients"],
                hparams["init_prev_count"],
                hparams["max_distance"],
                hparams["capacity_thresh"],
            )
            node_dict[node_lab] = new_node

        return node_dict

    def within_reach(self, node_lab, which):
        # Get list of target nodes within reach
        source_idx = self.node_list.index(node_lab)
        dist_row = np.squeeze(np.asarray(self.distance_matrix[source_idx, :]))
        target_idxs = (
            dist_row < self.hospi_nodes[node_lab].max_distance[which]
        ).astype(int)
        target_nodes = [
            tnode_lab
            for i, tnode_lab in enumerate(self.node_list)
            if target_idxs[i] and tnode_lab != node_lab
        ]
        return target_nodes

    def add_new_patients(self, df):
        # For each department
        for idx, row in df.iterrows():
            # Compute incoming patients and update patient count
            if row.dep in self.node_list:
                self.hospi_nodes[row.dep].add_new_patients(
                    {"icu": row.rea, "acute": row.hosp - row.rea}
                )
        return

    def redistribute_patients_by_type(self, node_lab, which):
        # dictionary for the patient count updates
        transfer_dict = {"icu": 0, "acute": 0}

        # compute number of patients over capacity - what we would like to transfer
        over_threshold = self.hospi_nodes[node_lab].over_capacity(which)

        # find a suitable hospital using shortest path and check if they can take the patients
        target_nodes = self.within_reach(node_lab, which)

        # loop over other nodes by distance < max_distance - ask node for availability
        for target_lab in target_nodes:
            if over_threshold == 0:
                break
            target_avail = self.hospi_nodes[target_lab].availability(which=which)
            if target_avail > 0:
                # if ok then tranfer -> update n_patients in nodes; found = True
                patients_to_transfer = min(target_avail, over_threshold)
                transfer_dict[which] = patients_to_transfer
                self.hospi_nodes[target_lab].add_incoming_patients(transfer_dict)
                self.hospi_nodes[node_lab].remove_outgoing_patients(transfer_dict)
                over_threshold -= patients_to_transfer
        return

    def redistribute_patients(self, return_counts=False):
        # dictionary to store information about each node
        network_state = {}
        for node_lab, _ in self.degree_orders:
            # check if occupancy_perc > capacity_thresh:
            if self.hospi_nodes[node_lab].over_capacity("icu") > 0:
                self.redistribute_patients_by_type(node_lab, which="icu")
            if self.hospi_nodes[node_lab].over_capacity("acute") > 0:
                self.redistribute_patients_by_type(node_lab, which="acute")
            network_state[node_lab] = {
                "occupancy%": {
                    "total": self.hospi_nodes[node_lab].occupancy_percentage("all"),
                    "icu": self.hospi_nodes[node_lab].occupancy_percentage("icu"),
                    "acute": self.hospi_nodes[node_lab].occupancy_percentage("acute"),
                }
            }
            if return_counts:
                network_state[node_lab]["n_patients"] = {
                    "icu": self.hospi_nodes[node_lab].n_patients["icu"],
                    "acute": self.hospi_nodes[node_lab].n_patients["acute"],
                }

        return network_state
