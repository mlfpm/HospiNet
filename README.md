# HospiNet
Hospital Network Simulations in France

@authors

Bowen Fan, ETH Zürich, Switzerland, bowen.fan@bsse.ethz.ch

Ndèye Maguette Mbaye, ARMINES/Mines ParisTech, France,  ndeye-maguette.mbaye@mines-paristech.fr

Lucas Miranda,  Max Planck Institute of Psychiatry, Germany,  lucas_miranda@psych.mpg.de

Giulia Muzio, ETH Zürich, Switzerland,  giulia.muzio@bsse.ethz.ch

Emese Sukei,  Universidad Carlos III de Madrid, Spain,  esukei@ing.uc3m.es

Giovanni Visonà,  Max Planck Institute for Intelligent Systems, Germany,  giovanni.visona@tuebingen.mpg.de


Authors are ESRs in MLFPM project https://mlfpm.eu/



## Background
Our project is named HospiNet. With Hospinet we aim to simulate the French hospitals’ load under this COVID-19 emergency. 

Useful links: https://hospinet.herokuapp.com/

In our simulations, we consider two scenarios. The first scenario simply shows current statistics. These are the incoming patients in acute and icu care, patients coming into a hospital, stay in that hospital. In the second one, we allow the movement of patients from one hospital to another. Moving patients happens when a hospital reaches a threshold capacity. Target hospitals will only accept patients when they are under their own threshold capacity. Targets are selected within a predefined radius, in order of closest to furthest.

## Usage
_Data_Processing.ipynb_
Notebook for calculating the distance and connectivity each two nodes to create the graph data.

_Data_Visualisations.ipynb_
Visulization of the beds numbers and also the daily patients flow for each Department.

_Graph_Visualisation.ipynb_
Visualization of the netwokr of the Franch departments


