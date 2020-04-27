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

    def __init__(self, label, n_beds, max_distance, capacity_thresh):
        self.label = label  # label in the France_graph
        self.n_beds = n_beds  # dictionary - {‘icu’, ‘normal’}
        self.max_distance = copy.deepcopy(max_distance)
        self.capacity_thresh = copy.deepcopy(capacity_thresh)
        self.n_icu_patients = 0
        self.n_acute_patients = 0
        self.prev_icu_patients = 0
        self.prev_acute_patients = 0

    def in_daily_patients(self, new_icu, new_acute):
        self.n_icu_patients += new_icu - self.prev_icu_patients
        self.n_acute_patients += new_acute - self.prev_acute_patients
        self.prev_icu_patients = new_icu
        self.prev_acute_patients = new_acute
        return

    def in_transfer_patients(self, in_patients, which):
        if which == "icu":
            self.n_icu_patients += in_patients
        else:
            self.n_acute_patients += in_patients
        return

    def out_transfer_patients(self, out_patients, which):
        if which == "icu":
            self.n_icu_patients -= out_patients
        else:
            self.n_acute_patients -= out_patients
        return

    def over_capacity(self, which):
        # the number of patients that are over capacity by unit: "acute", "icu", this is what we would like to transfer
        if which == "icu":
            return np.ceil(
                self.n_icu_patients - (self.capacity_thresh[which] * self.n_beds[which])
            )
        else:
            return np.ceil(
                self.n_acute_patients
                - (self.capacity_thresh[which] * self.n_beds[which])
            )

    def availability(self, which):
        # the number of patients by unit: "acute", "icu" that we can accept without going over capacity
        if which == "icu":  # perform the calculation on everything
            availability = (
                self.capacity_thresh[which] * self.n_beds[which]
            ) - self.n_icu_patients
        else:  # perform the calculation only for the chosen kind of bed: "acute", "icu"
            availability = (
                self.capacity_thresh[which] * self.n_beds[which]
            ) - self.n_acute_patients

        return np.floor(availability) if availability > 0 else 0

    @property
    def occupancy_percentage(self):
        # percentage of occupied beds, perform the calculation only for the chosen kind of bed
        return {
            "icu": (self.n_icu_patients / self.n_beds["icu"]) * 100.0,
            "acute": (self.n_acute_patients / self.n_beds["acute"]) * 100.0,
            "total": (self.total_patients / self.total_beds) * 100.0,
        }

    @property
    def n_patients(self):
        return {
            "icu": self.n_icu_patients,
            "acute": self.n_acute_patients,
            "total": self.total_patients,
        }

    @property
    def total_beds(self):
        return self.n_beds["icu"] + self.n_beds["acute"]

    @property
    def total_patients(self):
        return self.n_icu_patients + self.n_acute_patients


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
        france_graph = hparams["france_graph"]

        # get list of nodes ordered ascending degrees
        self.degree_orders = list(france_graph.degree)
        self.degree_orders.sort(key=operator.itemgetter(1))

        # get list of node labels
        self.node_list = list(france_graph.nodes)

        # compute shortest paths distance_matrix
        self.distance_matrix = nx.floyd_warshall_numpy(france_graph, weight="distance")

        # generate the HospiNodes

        # Read bed info from file
        with open(hparams["attr_path"], "rb") as handle:
            bed_info = pickle.load(handle)

        # Create a custom node dictionary
        self.hospi_nodes = {}
        for i, node_lab in enumerate(self.node_list):
            self.hospi_nodes[node_lab] = HospiNode(
                node_lab,
                bed_info[node_lab]["beds"],
                hparams["max_distance"],
                hparams["capacity_thresh"],
            )

        return

    def in_daily_patients_all_nodes(self, df):
        # For each department
        for idx, row in df.iterrows():
            # Compute incoming patients and update patient count
            if row.dep in self.node_list:
                n_icu = row.rea
                n_acute = row.hosp - row.rea
                self.hospi_nodes[row.dep].in_daily_patients(n_icu, n_acute)

        return

    def redistribute_patients(self):
        # for each node in ascending degree order
        for node_lab, _ in self.degree_orders:
            # check if occupancy_perc > capacity_thresh:
            if self.hospi_nodes[node_lab].over_capacity("icu") > 0:
                self.redistribute_patients_by_type(node_lab, which="icu")
            if self.hospi_nodes[node_lab].over_capacity("acute") > 0:
                self.redistribute_patients_by_type(node_lab, which="acute")
        return

    def redistribute_patients_by_type(self, source_lab, which):
        # compute number of patients over capacity - what we would like to transfer
        over_threshold = self.hospi_nodes[source_lab].over_capacity(which)

        # find a suitable hospital using shortest path and check if they can take the patients
        target_labels = self.get_target_nodes(source_lab, which)

        # loop over other nodes by distance < max_distance - ask node for availability
        for target_lab in target_labels:
            if over_threshold == 0:
                break
            target_avail = self.hospi_nodes[target_lab].availability(which=which)
            if target_avail > 0:
                # if ok then tranfer -> update n_patients in nodes; found = True
                patients_to_transfer = min(target_avail, over_threshold)
                self.hospi_nodes[target_lab].in_transfer_patients(
                    patients_to_transfer, which
                )
                self.hospi_nodes[source_lab].out_transfer_patients(
                    patients_to_transfer, which
                )
                over_threshold -= patients_to_transfer
        return

    def get_target_nodes(self, source_lab, which):
        # Get list of target nodes within reach
        source_idx = self.node_list.index(source_lab)
        dist_row = np.squeeze(np.asarray(self.distance_matrix[source_idx, :]))
        target_idxs = (
            dist_row < self.hospi_nodes[source_lab].max_distance[which]
        ).astype(int)
        target_nodes = [
            tnode_lab
            for i, tnode_lab in enumerate(self.node_list)
            if target_idxs[i] and tnode_lab != source_lab
        ]
        return target_nodes

    def get_network_state(self):
        # Return the state of each node (occupancy% and n_patients)
        network_state = {}
        # for each node in ascending degree order
        for node_lab, _ in self.degree_orders:
            # add return info to the dictionary
            network_state[node_lab] = {
                "occupancy%": self.hospi_nodes[node_lab].occupancy_percentage
            }
            network_state[node_lab]["n_patients"] = self.hospi_nodes[
                node_lab
            ].n_patients
        return network_state
