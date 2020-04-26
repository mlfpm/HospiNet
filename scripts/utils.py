# @authors: semese, lucasmiranda42

import os, pickle
import numpy as np
import pandas as pd
import plotly.express as px

from scripts.classes import HospiGraph

paths_dict = {
    "graph_path": os.path.abspath(
        os.path.join("data", "processed_data", "connectivity.pkl")
    ),
    "fullgraph_path": os.path.abspath(
        os.path.join("data", "processed_data", "France_graph.pkl")
    ),
    "dist_path": os.path.abspath(
        os.path.join("data", "processed_data", "distances_times.pkl")
    ),
    "attr_path": os.path.abspath(
        os.path.join("data", "processed_data", "departments.pkl")
    ),
    "time_series_path": os.path.abspath(
        os.path.join("data", "France_Hospital_data", "date_dep.csv")
    ),
    "bed_info_path": os.path.abspath(
        os.path.join("data", "raw_data", "bed_per_dep.pkl")
    ),
}


def on_submit_call(max_dist_dict: dict, cap_thresh_dict: dict, simulation: bool):
    """
        Method called on Submit button press. It computes the simulation or just
        the evolution of data over time based on the value of the ´simulation´
        argument.
        Args:
            max_dist_dict (dictionary) - the maximum distances to transfer patients to
            cap_thresh_dict (dictionary) - the capacity threshold for each department
            simulation (bool) - flag for running the simulation
        Returns:
            time_df (DataFrame) - a dataframe containing the occupancy rate and
                patient count over time for each department
    """
    if simulation:
        time_df = set_up_simulation(max_dist_dict, cap_thresh_dict)
    else:
        time_df = occupancy_rate_over_time()
    return time_df


def occupancy_rate_over_time():
    """
        Method to compute the occupancy rate over time if the simulation is not
        activated.
        Returns:
             output (DataFrame) - containing the daily stats for all the departments
    """
    # Read time series data
    df = pd.read_csv(paths_dict["time_series_path"])

    # Load distances and times
    with open(paths_dict["bed_info_path"], "rb") as handle:
        bed_info = pickle.load(handle)

    # Set date to datetime type
    df["jour"] = pd.to_datetime(df["jour"], format="%Y/%m/%d")
    df["dep"] = df["dep"].str.zfill(2)

    # Dictionary to store the results
    output = {}

    # For each time point
    for date in df["jour"].sort_values().unique():
        temp = {}
        time_series_df = df[df["jour"] == date]
        # For each department
        for idx, row in time_series_df.iterrows():
            # Get occupancy and patient count in that time step
            temp[row.dep] = {
                "n_patients": {"icu": row.rea, "acute": row.hosp - row.rea},
                "occupancy%": {
                    "total": (
                        row.hosp
                        / (bed_info[row.dep]["icu"] + bed_info[row.dep]["acute"])
                    )
                    * 100.0,
                    "icu": (row.rea / bed_info[row.dep]["icu"]) * 100.0,
                    "acute": ((row.hosp - row.rea) / bed_info[row.dep]["acute"])
                    * 100.0,
                },
            }
        output[np.datetime_as_string(date, unit="D")] = temp

    return dict_to_df(output)


def set_up_simulation(max_dist_dict, cap_thresh_dict):
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
        **paths_dict,
        **{
            "init_n_patients": {"icu": 0, "acute": 0},
            "init_prev_count": {"icu": 0, "acute": 0},
            "max_distance": max_dist_dict,
            "capacity_thresh": cap_thresh_dict,
        },
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
            output (DataFrame) - the occupancy level by day for each department
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

    return dict_to_df(output)


def dict_to_df(output):
    """
        Method to transform the output dictionary of the time series information into
        a pandas DataFrame
        Args:
            output (dictionary) - the occupancy level by day for each department
        Returns:
            output (DataFrame) -  the dictionary transformed into a dataframe
    """
    result_dict = {
        "Date": [],
        "dep": [],
        "total_occupancy": [],
        "icu_occupancy": [],
        "acute_occupancy": [],
        "icu_patients": [],
        "acute_patients": [],
    }

    for Date, val in output.items():
        for node in val:
            result_dict["Date"].append(Date)
            result_dict["dep"].append(node)
            result_dict["total_occupancy"].append(val[node]["occupancy%"]["total"])
            result_dict["icu_occupancy"].append(val[node]["occupancy%"]["icu"])
            result_dict["acute_occupancy"].append(val[node]["occupancy%"]["acute"])
            result_dict["icu_patients"].append(val[node]["n_patients"]["icu"])
            result_dict["acute_patients"].append(val[node]["n_patients"]["acute"])

    return pd.DataFrame(result_dict)


def animate_graph(time_df, animate: str, style="carto-positron"):
    """
    Method to plot an animated simulation using a given data-set using a predefined network.
        time_df (DataFrame) - the output of the ´on_submit_call´ method
        animate (string) - the name of the variable to animate in the resulting plot.
            Should be one of ["total_occupancy","icu_occupancy","acute_occupancy",
            "icu_patients","acute_patients"]
        style (string, optional) - style that ploly should use to render the map.

            Should be one of ['open-street-map','white-bg','carto-positron',
             'carto-darkmatter','stamen-terrain','stamen-toner','stamen-watercolor',
             'basic','streets','outdoors', 'light','dark', 'satellite','satellite-streets]

    Returns:
        fig (plotly figure) - animation of 'animate' parameter over time on the map
        to visualise, call the .show() method on the returned object
    """

    with open(paths_dict["fullgraph_path"], "rb") as handle:
        G = pickle.load(handle)

    df = {"dep": [], "name": [], "lat": [], "lon": [], "icu": []}
    for node in G.nodes():
        df["dep"].append(node)
        df["name"].append(G.nodes[node]["name"])
        df["lat"].append(G.nodes[node]["coords"]["lat"])
        df["lon"].append(G.nodes[node]["coords"]["lng"])
        df["icu"].append(G.nodes[node]["icu"])

    df = pd.DataFrame(df)
    df = pd.merge(df, time_df, how="outer").fillna(10)
    df["Date"] = pd.to_datetime(df.Date.astype(str)).astype(str)
    df.sort_values(["Date", "lat", "lon"], inplace=True)

    edge_x = []
    edge_y = []
    for edge in G.edges():
        y0, x0 = G.nodes[edge[0]]["coords"].values()
        y1, x1 = G.nodes[edge[1]]["coords"].values()
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        center={"lat": 46.7111, "lon": 1.7191},
        color=animate,
        size=animate,
        mapbox_style=style,
        animation_frame="Date",
        color_continuous_scale="bluered",
        size_max=55,
        zoom=5,
        opacity=0.6,
        hover_name="name",
        # width=800,
        # height=800,
    )

    fig.add_scattermapbox(
        lon=edge_x,
        lat=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="text",
        mode="lines",
        opacity=0.4,
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
        transition={"duration": 1, "easing": "linear"},
    )

    return fig


def plot_occupancy_evolution(time_df, what_to_plot, department_label):
    """
    Method to plot the evolution of a given parameter for a given department.
        time_df (DataFrame) - the output of the ´on_submit_call´ method
        what_to_plot (string) - the name of the variable to show in the resulting plot.
            Should be one of ["total_occupancy","icu_occupancy","acute_occupancy",
            "icu_patients","acute_patients"]
        department_label (string) - the label of the department for which to plot the
            graph
    Returns:
        fig (plotly figure) - the graph
    """
    df = time_df[time_df["dep"] == department_label]
    fig = px.line(df, x="Date", y=what_to_plot)
    return fig
