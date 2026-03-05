# Taxi Service Data Engineering & Analytics Project
## Using GCP | Mage | BigQuery | Looker

## The Introduction & Technology Breakdown
### Introduction
I engineered a scalable, cloud-native ETL pipeline on Google Cloud Platform to automate the end-to-end lifecycle of raw Taxi datasets. By architecting a robust extraction and transformation workflow, I converted fragmented data into a structured analytical model. To maximize performance, I developed a denormalized reporting layer using joins in SQL in BigQuery where I merged complex multi-dimensional entities into a high-speed selection table which is specifically optimized for seamless, low-latency integration with Looker Studio for data analysis.

### Technology Stack
•	**Google Cloud Storage:** Acts as the primary data lake for securely staging raw Taxi datasets before processing.

•	**Google Compute Engine:** Provides the high-performance virtual environment required to run data scripts and host the pipeline infrastructure.

•	**Mage Data Pipeline:** Serves as the modern orchestration tool to automate and monitor the ETL (Extract, Transform, Load) workflow.

•	**Python:** Used as the core programming language to perform complex data cleaning and dimensional modeling via custom scripts.

•	**Google BigQuery:** Utilized as a serverless data warehouse to store structured Fact and Dimension tables for high-speed SQL querying.

**SQL:** To perform complex joins and create the final analytical table for reporting.

•	**Looker Studio:** Functions as the visualization layer to transform BigQuery data into interactive, actionable business dashboards.



## Architecture 
![Taxi Data Engineering Project Architect](https://drive.google.com/uc?export=view&id=1mridvJgLHLHw2H7XzlTX-6n_DskgJALj)

## Technology Used
- Programming Language - Python

Google Cloud Platform
1. Google Storage
2. Compute Instance 
3. BigQuery
4. Looker Studio

Modern Data Pipeine Tool - https://www.mage.ai/

## Dataset Used
TLC Trip Record Data
Yellow and green taxi trip records include fields capturing pick-up and drop-off dates/times, pick-up and drop-off locations, trip distances, itemized fares, rate types, payment types, and driver-reported passenger counts. 

More info about dataset can be found here:
1. Website - https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
2. Data Dictionary - https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

## Data Model
I architected a structured Star Schema by transforming raw Uber data into optimized Fact and Dimension tables. Using Python, I engineered custom indexing for each dimension table which includes temporal, geospatial, and payment attributes. This significantly enhances query performance and computational efficiency. The central Fact Table integrates critical metrics such as trip distances and itemized fares with relational keys for pick-up/drop-off logistics and passenger data. This normalized structure, enriched with calculated analytical columns, serves as a high-performance foundation for complex data analysis and seamless integration with BigQuery and Looker Studio

![Taxi Data Engineering Project Data Model](https://drive.google.com/uc?export=view&id=1uwXj1Fdwy4hid4zzu4JcLHak_bGbL7z6)
