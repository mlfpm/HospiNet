# HospiNet
Hospital Network Simulations in France

Our project is named HospiNet. With Hospinet we aim to simulate the French hospitals’ load under this covid-19 emergency. 

Useful links: https://hospinet.herokuapp.com/

In our approach, France is represented as a graph: each node is the prefecture of each French department, and two nodes are connected through an edge in case the corresponding departments geographically border.
In our simulations, we consider two scenarios. In the first one, we allow the movement of patients from a hospital to another one. Specifically, we model the movement if the ‘origin’ hospital is overloaded, namely the number of occupied beds is higher than a predefined load threshold. Instead, the ‘arrival’ hospital has a load which permits it to receive these patients. The second scenario, instead, does include the patients’ move just described.


## Datasets

Four Datasets from distinct sources were used. 

> ### Hospital dataset

*This dataset comes from a COVID-19 certified public service*

In response to the COVID-19 pandemic, the french public data open platform [Santé publique France](https://www.data.gouv.fr) has made available daily reports dataset of the ongoing hospitals' situation on the National territory. 

The reporting system is not exhaustive, hence the number of reporting establishments in a department varies over time.Also, some patients, that have been reported at one point, may be taken of the health structures' database whether the biological came back negative to COVID-19. 

We use two of the four datasets proposed.

1. [donnees-hospitalieres-covid19-2020-04-23-19h00.csv](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/donnees-hospitalieres-covid19-2020-04-23-19h00.csv)

   We used the hospitals' dataset on a department level and by sex. It informs the daily flow of COVID-19 patients. Each row of data reports cumulative number of cases, deaths or recovers for a specific department.
   The dataset contains 11215 samples and 7 features for the 101 departments of France.


````html
    "dep";"sexe";"jour";"hosp";"rea";"rad";"dc"
    "01";0;"2020-03-18";2;0;1;0
````


#### Field description :
- **dep** : French department code 
- **sexe** : Gender of the patient (0= Male + Female; 1= Male; 2= Female)
- **jour** : Date of the report (YYYY-MM-DD) 
- **hosp** : Cumulative Number of hospitalised patients
- **rea** : Cumulative Number of ICU/Resuscitation patients
- **rad** : Cumulative Number of people returned home 
- **dc** : Cumulative Number of deceased

#### Update Frequency 
From 2020-03-18 on, once per day at 19:00 (UTC+2).

#### Source
[here](https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/)


 
2. [donnees-hospitalieres-nouveaux-covid19-2020-04-23-19h00.csv](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/donnees-hospitalieres-nouveaux-covid19-2020-04-23-19h00.csv)

    This dataset is the report of new COVID-19 data each day. Data are not cumulative unlike the previous dataset. Each row   reports new cases, new deaths and new recovers for a specific department.
    The dataset contains 3637 samples and 6 features for the 101 departments of France.

````html
    dep;jour;incid_hosp;incid_rea;incid_dc;incid_rad
    01;2020-03-19;1;0;0;0
`````

- **dep** : French department code 
- **jour** : Date of the report (YYYY-MM-DD) 
- **incid_hosp** : Daily Number of hospitalised patients
- **incid_rea** : Daily Number of ICU/Resuscitation patients
- **incid_dc** : Daily Number of deceased
- **incid_rad** : Daily Number of people returned home 


#### Update Frequency 
From 2020-03-18 on, once per day at 19:00 (UTC+2).

#### Source
[here](https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/)


> ### Beds dataset 

The french government provides a health establishments annual statistics which is an exhaustive administrative inquiry from all health establishments in France (metropole and DOM TOM). It allows the detailed mapping of health establishments.
This [dataset](https://github.com/mlfpm/HospiNet/tree/master/data/raw_data). describes the number of beds' evolution between 2013 and 2018, in the french health establishments. We used the given number of beds in 2018 per department.

#### Field description 
- **Dep_code** : French department code
- **Dep** : Name of the department 
- **Rea** : Number of beds for rescusitation patients
- **ICU** : Number of beds for ICU patients
- **Continuous_care** : Number of beds for acute patients
- **Total** : Total Number of beds

#### Update Frequency
Annual update from 2000 to 2018.

#### Source 
[here](https://drees.solidarites-sante.gouv.fr/etudes-et-statistiques/publications/article/nombre-de-lits-de-reanimation-de-soins-intensifs-et-de-soins-continus-en-france)
 
> ### Number of population

The french population estimation is done by the [Insee](insee.fr) (Institut National de la Statistique et des Etudes Economiques), every 1st of january. The latest version (2020) of department level estimation is used. 

#### Update Frequency
Each year.
#### Source
[here](https://www.insee.fr/fr/statistiques/1893198)


> ### Distance Matrix

A distance matrix has been defined between the two main* cities of each department, with google API. It provides the travel distance and time for a matrix of origins and destinations, based on the recommended route between them.

*most populated


## Pre- processing 
> ### Graph Data

The connectivity of the graph (1st degree connection) is listed, then the distances and driving time between each two connected nodes were acquired via Google Maps API, together with the coordinates (centering on the capital of the department) and population of each department. The number of ICU and acute bed is also added to each node of the graph. The data is stored as python dictionary in the format of:

(data format here)
> ### Hospital Data

The hospital data contains anomalies and mismatches due to some data collection difficulties. The problem is mainly with the cumulative number of deceased patients/patients returned home may decrease over time. It is corrected based on the simple rule that, if the number is larger than the number of the next day, it will be replaced by the rounding average of the number from the days before and after. The data is sorted differently by date and department number as [date_dep.csv](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/dep_date.csv) and [dep_date.csv](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/dep_date.csv).
