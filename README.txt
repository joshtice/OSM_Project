The components of the OpenStreetMap project submission are distributed as follows:

OpenStreetMap_Project.ipynb
- Jupyter notebook used to generate OpenStreetMap_Project.html

OpenStreetMap_Project.html
- Answers to the rubric questions; Documentation of the data wrangling process
- Link to the map position, short description of the area, reason for the choice

Rochester_sample.osm
- .osm file containing a sample of the map region used

audit_tags.py
- Python code for auditing the OSM file
- References used to develop the script

osm_to_csv.py
- Python code for cleaning the OSM file and transferring to .csv files
- References used to develop the script

csv_to_database.py
- Python code for uploading .csv files to a database
- References used to develop the script

sql_queries.py
- Python code to perform queries on the database
- References used to develop the script

schema.py
- Schema for the database used for validation in the osm_to_csv.py script, downloaded
  from Udacity
  