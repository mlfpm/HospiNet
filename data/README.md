# Data Description
_This dataset comes from a COVID-19 certified public service_

In response to the COVID-19 pandemic, the french public data open platform [Santé publique France](https://www.data.gouv.fr/fr/) has made available daily reports a dataset of the ongoing hospitals' situation on the National territory.
The reporting system is not exhaustive, hence the number of reporting establishments in a department varies over time.Also, some patients that have been reported at one point, may be taken off the health structures' database whether the biological came back negative to COVID-19.

We two of the four datasets acquired from the platform:

[Dataset 1](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/donnees-hospitalieres-covid19-2020-04-23-19h00.csv)

This dataset is on a department level and by sex. It contains 11215 samples and 7 features for the 101 departments of France.


   _Field Description_
   
    dep : French department code
    sexe : Gender of the patient (0= Male + Female; 1= Male; 2= Female)
    jour : Date of the report (YYYY-MM-DD)
    hosp : Cumulative Number of hospitalised patients
    rea : Cumulative Number of ICU/Resuscitation patients
    rad : Cumulative Number of people returned home
    dc : Cumulative Number of deceased
 
 The update frequency of the data is everyday on 19:00 (UTC+2) from 2020-03-18.
 
[Dataset 2](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/donnees-hospitalieres-nouveaux-covid19-2020-04-23-19h00.csv)

This dataset is the report of new COVID-19 data each day. Data is not cumulative unlike the previous dataset. Each row reports new cases, new deaths and new recovers for a specific department. The dataset contains 3637 samples and 6 features for the 101 departments of France.

   _Field Description_
   
    dep : French department code
    jour : Date of the report (YYYY-MM-DD)
    incid_hosp : Daily number of hospitalised patients
    incid_rea : Daily number of ICU/Resuscitation patients
    incid_dc : Daily number of deceased
    incid_rad : Daily number of people returned home

The update frequency of the data is everyday on 19:00 (UTC+2) from 2020-03-18.

[Dataset 3](https://github.com/mlfpm/HospiNet/blob/master/data/raw_data/bed_per_dep.pkl)

We also used the dataset describes the number of beds' evolution between 2013 and 2018, in the french health establishments and selected the given number of beds in 2018 per department. This data is provided by the [french government](https://drees.solidarites-sante.gouv.fr/etudes-et-statistiques/publications/article/nombre-de-lits-de-reanimation-de-soins-intensifs-et-de-soins-continus-en-france).

   _Field Description_
   
    Dep_code : French department code
    Dep : Name of the department
    Rea : Number of beds for resuscitation patients
    ICU : Number of beds for ICU patients
    Continuous_care : Number of beds for acute patients
    Total : Total Number of beds
    
The update frequency of the data is every year from 2000 to 2018.

[Dataset 4](https://www.insee.fr/fr/statistiques/1893198)

The french population estimation is done by the Insee (Institut National de la Statistique et des Etudes Economiques), every 1st of january. The latest version (2020) of department level estimation is used. 

The update frequency of the data is every year.

## Data Pre-processing

The connectivity of the graph (1st degree connection) is listed, then the distances and driving time between each two connected nodes were acquired via Google Maps API, together with the coordinates (centering on the capital of the department) and population of each department. The number of ICU and acute bed is also added to each node of the graph.

The hospital data contains anomalies and mismatches due to some data collection difficulties. The problem is mainly with the cumulative number of deceased patients/patients returned home may decrease over time. It is corrected based on the simple rule that, if the number is larger than the number of the next day, it will be replaced by the rounding average of the number from the days before and after. The data is sorted differently by date and department number as [date_dep.csv](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/date_dep.csv) and [dep_date.csv](https://github.com/mlfpm/HospiNet/blob/master/data/France_Hospital_data/dep_date.csv).


