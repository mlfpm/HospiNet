# @author: gvisona

import sys
sys.path.insert(0,'..')

import flask
from flask import Flask, render_template, request
import plotly
import plotly.express as px
import plotly.graph_objs as go
import pickle
import os
import networkx as nx

import pandas as pd
import numpy as np
import json

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Output, Input, State

from scripts.utils import animate_graph, plot_occupancy_evolution, on_submit_call

time_df = pd.DataFrame()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "HospiNet"
server = app.server

app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.Div(
                            className="flex-row-between",
                            children=[
                                html.A(children=[html.Img(
                                    className="logo", src=app.get_asset_url("mlfpm_logo.png")
                                )], href='https://mlfpm.eu/', target="_blank"),
                                html.A(children=[html.Img(
                                    className="logo", src=app.get_asset_url("euvsvirus.jpg")
                                )], href='https://euvsvirus.org/', target="_blank")
                            ]
                        ),

                        html.H1("HospiNet"),
                        html.P(
                            """Simulate the load caused by the SARS-CoV-2 pandemic on the french hospital network. 
                            """
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Show Help",
                                    id="collapse-button",
                                    className="mb-3",
                                    color="secondary",
                                ),
                                dbc.Collapse(
                                    dbc.Card(dbc.CardBody(
                                        children=[html.P(
                                            """
                                            The 'Simulate' button allows you to 
                                            display the behaviour of the network with the selected parameters. 
                                            """
                                        ),
                                        html.P(
                                            """
                                            The checkbox below selects whether the simulation allows the transfer of patients between hospitals. If it is active,
                                            the user needs to select the threshold values of capacity for Acute and ICU patients beyond which a hospital will try to transfer
                                            some of the load to other hospitals. The Max Distance threshold selects how far a patient can travel in a transfer between hospitals. 
                                            """
                                        ),
                                        html.P(
                                            """
                                            The tabs at the top of the graphs allow you to switch between the global network graph animation and the visualization
                                            of the evolution for a specific department. 
                                            """
                                        )]
                                    ), color="dark", inverse=True),
                                    id="collapse",
                                    is_open=False
                                ),
                            ]
                        ),
                        # html.P(
                        #     """
                        #     The 'Simulate' button allows you to 
                        #     display the behaviour of the network with the selected parameters. 
                        #     """
                        # ),
                        # html.P(
                        #     """
                        #     The checkbox below selects whether the simulation allows the transfer of patients between hospitals. If it is active,
                        #     the user needs to select the threshold values of capacity for Acute and ICU patients beyond which a hospital will try to transfer
                        #     some of the load to other hospitals. The Max Distance threshold selects how far a patient can travel in a transfer between hospitals. 
                        #     """
                        # ),
                        # html.P(
                        #     """
                        #     The tabs at the top of the graphs allow you to switch between the global network graph animation and the visualization
                        #     of the evolution for a specific department. 
                        #     """
                        # ),
                        html.P(
                            """
                            For more info refer to:
                            """
                        ),
                        html.Ul(children=[
                            html.Li(children=[html.A(children=["The Devpost Submission"], href='https://devpost.com/software/hospinet', target="_blank"),]),
                            html.Li(children=[html.A(children=["Our Github Repo"], href='https://github.com/mlfpm/HospiNet', target="_blank"),]),
                        ]),
                        

                        
                        
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                dcc.Checklist(id="checkbox", className="checkboxes",
                                              options=[
                                                  {'label': ' Allow transfer of patients between hospitals',
                                                   'value': 'prop_bool'},
                                              ],
                                              value=[]
                                              )
                            ],
                        ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[html.Label(
                                        'Quantity To Show'),
                                dcc.Dropdown(
                                    id='animate-dropdown',
                                    options=[
                                        {"label": "Total Occupancy",
                                            "value": "total_occupancy"},
                                        {"label": "ICU Occupancy",
                                            "value": "icu_occupancy"},
                                        {"label": "Acute Occupancy",
                                            "value": "acute_occupancy"},
                                        {"label": "Total Patients",
                                            "value": "total_patients"},                                            
                                        {"label": "ICU Patients",
                                            "value": "icu_patients"},
                                        {"label": "Acute Patients",
                                            "value": "acute_patients"},
                                        ],
                                    value='total_occupancy',
                                    clearable=False
                                )
                            ],
                        ),
                        html.Div(id='form_div',
                                 className="div-for-dropdown",
                                 children=[
                                     html.H3("Thresholds"),
                                    html.Div(className="flex-row",
                                    children=[html.Label(
                                         'Capacity (%)'),
                                        html.Div(className="input-with-label",
                                        children=[
                                             html.Label(
                                            'Acute'),
                                            dcc.Input(
                                                id="capacity_acute_threshold", type="number", value=75,
                                                min=1, max=100, step=1
                                        )
                                        ]),
                                        html.Div(className="input-with-label",
                                        children=[
                                            html.Label('ICU'),
                                        dcc.Input(
                                            id="capacity_icu_threshold", type="number", value=75,
                                            min=1, max=100, step=1
                                        )
                                        ])
                                    ]),
                                    html.Div(className="flex-row",
                                    children=[html.Label(
                                         'Max Distance (km)'),
                                        html.Div(className="input-with-label",
                                        children=[
                                             html.Label(
                                            'Acute'),
                                            dcc.Input(
                                         id="distance_acute_threshold", type="number", value=500,
                                         min=100, max=3000, step=20
                                        )
                                        ]),
                                        html.Div(className="input-with-label",
                                        children=[
                                            html.Label('ICU'),
                                        dcc.Input(
                                         id="distance_icu_threshold", type="number", value=500,
                                         min=100, max=1000, step=20
                                        )
                                        ])
                                    ]),

                                 ], style={"display": "none"}
                                 ),
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.Button(
                                    'Simulate', id='submit-val', n_clicks=0),
                            ],
                        ),
                    ],
                ),
                # Column for app graphs and plots
                html.Div(
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        dcc.Tabs(id='tabs-selector', value='ng', children=[
                            dcc.Tab(label='Network Graph', value='ng'),
                            dcc.Tab(label='Department Details', value='occupancy'),
                        ]),
                        html.Div(id='graph_div', style={"height": "100%"}),
                        html.Div(id="occupancy_tab",
                            #className="text-padding",
                            children=[
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        html.Label('Select a Department'),
                                dcc.Dropdown(
                                    id='department-dropdown',
                                    options=[
                                        {"label": "01 - Ain - Bourg-en-Bresse",
                                            "value": "01"},
                                        {"label": "02 - Aisne - Laon",
                                            "value": "02"},
                                        {"label": "03 - Allier - Moulins",
                                            "value": "03"},
                                        {"label": "04 - Alpes-de-Haute-Provence - Digne",
                                            "value": "04"},
                                        {"label": "05 - Hautes-Alpes - Gap",
                                            "value": "05"},
                                        {"label": "06 - Alpes Maritimes - Nice",
                                            "value": "06"},
                                        {"label": "07 - Ardèche - Privas",
                                            "value": "07"},
                                        {"label": "08 - Ardennes - Charleville-Mézières",
                                            "value": "08"},
                                        {"label": "09 - Ariège - Foix",
                                            "value": "09"},
                                        {"label": "10 - Aube - Troyes",
                                            "value": "10"},
                                        {"label": "11 - Aude - Carcassonne",
                                            "value": "11"},
                                        {"label": "12 - Aveyron - Rodez",
                                            "value": "12"},
                                        {"label": "13 - Bouches-du-Rhône - Marseille",
                                            "value": "13"},
                                        {"label": "14 - Calvados - Caen",
                                            "value": "14"},
                                        {"label": "15 - Cantal - Aurillac",
                                            "value": "15"},
                                        {"label": "16 - Charente - Angoulême",
                                            "value": "16"},
                                        {"label": "17 - Charente-Maritime - La Rochelle",
                                            "value": "17"},
                                        {"label": "18 - Cher - Bourges",
                                            "value": "18"},
                                        {"label": "19 - Corrèze - Tulle",
                                            "value": "19"},
                                        {"label": "21 - Côte-d'Or - Dijon",
                                            "value": "21"},
                                        {"label": "22 - Côtes d'Armor - St-Brieuc",
                                            "value": "22"},
                                        {"label": "23 - Creuse - Guéret",
                                            "value": "23"},
                                        {"label": "24 - Dordogne - Périgueux",
                                            "value": "24"},
                                        {"label": "25 - Doubs - Besançon",
                                            "value": "25"},
                                        {"label": "26 - Drôme - Valence",
                                            "value": "26"},
                                        {"label": "27 - Eure - Evreux",
                                            "value": "27"},
                                        {"label": "28 - Eure-et-Loir - Chartres",
                                            "value": "28"},
                                        {"label": "29 - Finistère - Quimper",
                                            "value": "29"},
                                        {"label": "30 - Gard - Nîmes",
                                            "value": "30"},
                                        {"label": "31 - Haute Garonne - Toulouse",
                                            "value": "31"},
                                        {"label": "32 - Gers - Auch", "value": "32"},
                                        {"label": "33 - Gironde - Bordeaux",
                                            "value": "33"},
                                        {"label": "34 - Hérault - Montpellier",
                                            "value": "34"},
                                        {"label": "35 - Ille-et-Vilaine - Rennes",
                                            "value": "35"},
                                        {"label": "36 - Indre - Châteauroux",
                                            "value": "36"},
                                        {"label": "37 - Indre-et-Loire - Tours",
                                            "value": "37"},
                                        {"label": "38 - Isère - Grenoble",
                                            "value": "38"},
                                        {"label": "39 - Jura - Lons-le-Saunier",
                                            "value": "39"},
                                        {"label": "40 - Landes - Mont-de-Marsan",
                                            "value": "40"},
                                        {"label": "41 - Loir-et-Cher - Blois",
                                            "value": "41"},
                                        {"label": "42 - Loire - St-Étienne",
                                            "value": "42"},
                                        {"label": "43 - Haute Loire - Le Puy",
                                            "value": "43"},
                                        {"label": "44 - Loire Atlantique - Nantes",
                                            "value": "44"},
                                        {"label": "45 - Loiret - Orléans",
                                            "value": "45"},
                                        {"label": "46 - Lot - Cahors",
                                            "value": "46"},
                                        {"label": "47 - Lot-et-Garonne - Agen",
                                            "value": "47"},
                                        {"label": "48 - Lozère - Mende",
                                            "value": "48"},
                                        {"label": "49 - Maine-et-Loire - Angers",
                                            "value": "49"},
                                        {"label": "50 - Manche - St-Lô",
                                            "value": "50"},
                                        {"label": "51 - Marne - Châlons-sur-Marne",
                                            "value": "51"},
                                        {"label": "52 - Haute Marne - Chaumont",
                                            "value": "52"},
                                        {"label": "53 - Mayenne - Laval",
                                            "value": "53"},
                                        {"label": "54 - Meurthe-et-Moselle - Nancy",
                                            "value": "54"},
                                        {"label": "55 - Meuse - Bar-le-Duc",
                                            "value": "55"},
                                        {"label": "56 - Morbihan - Vannes",
                                            "value": "56"},
                                        {"label": "57 - Moselle - Metz",
                                            "value": "57"},
                                        {"label": "58 - Nièvre - Nevers",
                                            "value": "58"},
                                        {"label": "59 - Nord - Lille",
                                            "value": "59"},
                                        {"label": "60 - Oise - Beauvais",
                                            "value": "60"},
                                        {"label": "61 - Orne - Alençon",
                                            "value": "61"},
                                        {"label": "62 - Pas-de-Calais - Arras",
                                            "value": "62"},
                                        {"label": "63 - Puy-de-Dôme - Clermont-Ferrand",
                                            "value": "63"},
                                        {"label": "64 - Pyrénées Atlantiques - Pau",
                                            "value": "64"},
                                        {"label": "65 - Hautes Pyrénées - Tarbes",
                                            "value": "65"},
                                        {"label": "66 - Pyrénées Orientales - Perpignan",
                                            "value": "66"},
                                        {"label": "67 - Bas-Rhin - Strasbourg",
                                            "value": "67"},
                                        {"label": "68 - Haut-Rhin - Colmar",
                                            "value": "68"},
                                        {"label": "69 - Rhône - Lyon",
                                            "value": "69"},
                                        {"label": "70 - Haute Saône - Vesoul",
                                            "value": "70"},
                                        {"label": "71 - Saône-et-Loire - Mâcon",
                                            "value": "71"},
                                        {"label": "72 - Sarthe - Le Mans",
                                            "value": "72"},
                                        {"label": "73 - Savoie - Chambéry",
                                            "value": "73"},
                                        {"label": "74 - Haute Savoie - Annecy",
                                            "value": "74"},
                                        {"label": "75 - Paris - Paris",
                                            "value": "75"},
                                        {"label": "76 - Seine Maritime - Rouen",
                                            "value": "76"},
                                        {"label": "77 - Seine-et-Marne - Melun",
                                            "value": "77"},
                                        {"label": "78 - Yvelines - Versailles",
                                            "value": "78"},
                                        {"label": "79 - Deux-Sèvres - Niort",
                                            "value": "79"},
                                        {"label": "80 - Somme - Amiens",
                                            "value": "80"},
                                        {"label": "81 - Tarn - Albi", "value": "81"},
                                        {"label": "82 - Tarn-et-Garonne - Montauban",
                                            "value": "82"},
                                        {"label": "83 - Var - Toulon",
                                            "value": "83"},
                                        {"label": "84 - Vaucluse - Avignon",
                                            "value": "84"},
                                        {"label": "85 - Vendée - La Roche-sur-Yon",
                                            "value": "85"},
                                        {"label": "86 - Vienne - Poitiers",
                                            "value": "86"},
                                        {"label": "87 - Haute Vienne - Limoges",
                                            "value": "87"},
                                        {"label": "88 - Vosges - Épinal",
                                            "value": "88"},
                                        {"label": "89 - Yonne - Auxerre",
                                            "value": "89"},
                                        {"label": "90 - Territoire de Belfort - Belfort",
                                            "value": "90"},
                                        {"label": "91 - Essonne - Evry",
                                            "value": "91"},
                                        {"label": "92 - Hauts-de-Seine - Nanterre",
                                            "value": "92"},
                                        {"label": "93 - Seine-St-Denis - Bobigny",
                                            "value": "93"},
                                        {"label": "94 - Val-de-Marne - Créteil",
                                            "value": "94"},
                                        {"label": "95 - Val-D'Oise - Pontoise",
                                            "value": "95"},
                                    ],
                                    value='75',
                                    clearable=False
                                )]),
                                html.Div(id='occupancy_div', style={"height": "90%"}),
                            ],
                        ),
                        
                    ],
                ),
            ],
        )
    ]
)


@app.callback(Output('form_div', 'style'), [Input('checkbox', 'value')])
def toggle_form(checkbox_value):
    if "prop_bool" in checkbox_value:
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback([Output('graph_div', 'children'), Output('occupancy_div', 'children')],
              [Input('submit-val', 'n_clicks'),
               Input('checkbox', 'value'),
               Input('animate-dropdown', 'value'),
               Input('department-dropdown', 'value')],
              [              
               State('capacity_acute_threshold', 'value'),
               State('capacity_icu_threshold', 'value'),
               State('distance_acute_threshold', 'value'),
               State('distance_icu_threshold', 'value')]
               )
def simulate(clicks, propagation_bool, animate_value, department_code, capacity_acute, capacity_icu, distance_acute, distance_icu,):
    #[{'prop_id': 'submit-val.n_clicks', 'value': 1}]
    # triggered:[{'prop_id': 'checkbox.value', 'value': [...]}]
    global time_df
    max_dist_dict = {"icu": distance_icu, "acute": distance_acute}
    cap_thresh_dict = {"icu": float(capacity_icu)/100, "acute": float(capacity_acute)/100}
    if dash.callback_context.triggered[0]["prop_id"] in ['checkbox.value','submit-val.n_clicks','.']:
        time_df = on_submit_call(max_dist_dict, cap_thresh_dict, propagation_bool)
    network_figure = animate_graph(time_df, animate_value, style="carto-positron")
    occupancy_figure = plot_occupancy_evolution(time_df, animate_value, str(department_code))
    return dcc.Graph(figure=network_figure, style={"width": "100%", "height":"100%"}), dcc.Graph(figure=occupancy_figure, style={"width": "100%", "height":"100%"})


# @app.callback([Output('occupancy_div', 'children')],
#               [Input('department-dropdown', 'value')],
#               [State('animate-dropdown', 'value')])
# def change_department(department_code, animate_value):
#     global time_df
#     occupancy_figure = plot_occupancy_evolution(time_df, animate_value, str(department_code))
#     return dcc.Graph(figure=occupancy_figure, style={"width": "100%"})



@app.callback([Output('graph_div', 'style'), Output('occupancy_tab', 'style')],
              [Input('tabs-selector', 'value')])
def select_tab(tab):
    if tab == 'ng':
        return ({'display': 'block', "height": "100%"}, {'display': 'none'})
    elif tab == 'occupancy':
        return ({'display': 'none'}, {'display': 'block', "height": "100%"})
    return ({'display': 'block'}, {'display': 'none'})


@app.callback(
    [Output("collapse", "is_open"), Output("collapse-button", "children")],
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        new_val = not is_open
        new_text = "Show Help" if not new_val else "Hide Help"
        return new_val, new_text
    new_val = is_open
    new_text = "Show Help" if not new_val else "Hide Help"
    return is_open, new_text

@server.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(server.root_path, 'assets'),
                                     'favicon.ico')


if __name__ == '__main__':
    app.run_server(debug=True)
