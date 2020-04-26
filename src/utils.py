import os
import numpy as np
import pandas as pd

from src.classes import HospiGraph


def start_simulation(max_dist_dict, cap_thresh_dict):
    """
        Method to run a simulation with a given parameter setting.
        To be called from the event-handler of the interface.
        Args:
            max_dist_dict (dictionary) - the maximum distances to transfer patients to
            cap_thresh_dict (dictionary) - the capacity threshold for each department
        Returns:
            network_state (dictionary) - the occupancy level by day for each department
    """
    # Initialise hparams
    hparams = {
        "graph_path": os.path.abspath(os.path.join("processed_data", "connectivity.pkl")),
        "dist_path": os.path.abspath(os.path.join("processed_data", "distances_times.pkl")),
        "attr_path": os.path.abspath(os.path.join("processed_data", "departments.pkl")),
        "init_n_patients": {"icu": 0, "acute": 0},
        "init_prev_count": {"icu": 0, "acute": 0},
        "max_distance": max_dist_dict,
        "capacity_thresh": cap_thresh_dict,
        "time_series_path": os.path.abspath(os.path.join("France_Hospital_data", "date_dep.csv")),
    }

    # Initialise network
    G = HospiGraph(hparams)

    # Read time series data
    df = pd.read_csv(hparams["time_series_path"])

    # Run the simulation
    network_state = run_simulation(df, G)

    return network_state


def run_simulation(df, G, return_counts=True):
    """
        Method to run simulation on a given data-set using a predefined network.
        Args:
            df (DataFrame) - pandas DataFrame having as columns:
                ['jour', 'dep', 'hosp', 'rea', 'rad', 'dc']
                (comes from /France_Hospital_data/date_dep.csv)
            G (HospiGraph) - an initialised HospiGraph object
            return_counts (bool) - flag to indicate whether to return
                the patient counts too or only the occupancy percentages
        Returns:
            output (dictionary) - the occupancy level by day for each department
    """
    # Set date to datetime type
    df["jour"] = pd.to_datetime(df["jour"], format="%Y/%m/%d")
    df["dep"] = df["dep"].str.zfill(2)

    # Dictionary to store the results
    output = {}

    # For each time point
    for date in df["jour"].sort_values().unique():
        # 1. Update incoming patient for each node
        time_series_df = df[df["jour"] == date]
        G.add_new_patients(time_series_df)

        # 2. For each node perform propagation - nodes are ordered by their degrees
        network_state = G.redistribute_patients(return_counts=return_counts)

        output[np.datetime_as_string(date, unit="D")] = network_state
    return output
