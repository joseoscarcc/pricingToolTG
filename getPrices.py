# import packages
import psycopg2
import pandas as pd
import datetime
import config
  
# establish connections
conn1 = psycopg2.connect(database=config.db,
                         host=config.hosting,
                         user=config.usuario,
                         password=config.contrasena,
                         port=config.puerto)
  
conn1.autocommit = True
cursor = conn1.cursor()
  
sql = "SELECT * FROM precios_site WHERE date = (SELECT MAX(date) FROM precios_site)"
sql2 = "SELECT * FROM precios_site WHERE date > now() - interval '30 day'"
precios = pd.read_sql_query(sql, conn1)
preciosHist = pd.read_sql_query(sql2,conn1)
conn1.commit()
conn1.close()

#get list of competencias
totalgasCompetencia = pd.read_csv('CompetenciaSites.csv')
listaPlaceID = totalgasCompetencia['place_id'].to_list()

#hacer df para trabajar
precios["place_id"] = precios["place_id"].apply(pd.to_numeric, errors='coerce')
preciosCompetencia = precios[precios['place_id'].isin(listaPlaceID)]

preciosHist["place_id"] = preciosHist["place_id"].apply(pd.to_numeric, errors='coerce')
preciosHistoricos = preciosHist[preciosHist['place_id'].isin(listaPlaceID)]