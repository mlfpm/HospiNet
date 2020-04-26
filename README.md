# HospiNet
Hospital Network Simulations in France

Our project is named HospiNet. With Hospinet we aim to simulate the French hospitals’ load under this covid-19 emergency. 

Useful links: https://hospinet.herokuapp.com/

In our approach, France is represented as a graph: each node is the prefecture of each French department, and two nodes are connected through an edge in case the corresponding departments geographically border.
In our simulations, we consider two scenarios. In the first one, we allow the movement of patients from a hospital to another one. Specifically, we model the movement if the ‘origin’ hospital is overloaded, namely the number of occupied beds is higher than a predefined load threshold. Instead, the ‘arrival’ hospital has a load which permits it to receive these patients. The second scenario, instead, does include the patients’ move just described.

# Usage
_Data_Processing.ipynb_
Notebook for calculating the distance and connectivity each two nodes to create the graph data.

_Data_Visualisations.ipynb_
Visulization of the beds numbers and also the daily patients flow for each Department.

_Graph_Visualisation.ipynb_
Visualization of the netwokr of the Franch departments


