from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, TEXT, Identity, inspect, select, update,insert
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
from datetime import datetime
import os

# NOTE: hardcoded RDS credentials removed for security. The old values remain in
# git history — that database's credentials must be rotated.
config={'DB_USER_NAME':os.environ.get('DB_USER_NAME'),
'DB_PASSWORD':os.environ.get('DB_PASSWORD'),
'DB_ADDRESS':os.environ.get('DB_HOST'),
'DB_NAME':os.environ.get('DB_NAME')}

engine=create_engine('postgresql://'+str(config.get('DB_USER_NAME'))+':'+str(config.get('DB_PASSWORD'))+'@'+str(config.get('DB_ADDRESS'))+':5432/'+str(config.get('DB_NAME')))
connection = engine.connect()
metadata = MetaData()
user_data = Table('User_Details', metadata, autoload_with=engine)

# Print the column names
print(user_data.columns.keys())

# Print full table metadata
print(repr(metadata.tables['User_Details']))

query = insert(user_data) 
values_list = [{'UserID':'dhanush@gmail.com', 'Password':'abcd', 'Name':'Dhanush', 'Plan':'Basic','Hit_count_left':10,'Updated_time':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
               {'UserID':'nishant@gmail.com', 'Password':'abcd', 'Name':'Nishant', 'Plan':'Standard','Hit_count_left':25,'Updated_time':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
               {'UserID':'shubham@gmail.com', 'Password':'abcd', 'Name':'Shubham', 'Plan':'Premium','Hit_count_left':50,'Updated_time':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
               ]

ResultProxy = connection.execute(query,values_list)
query=select(user_data.c.UserID,user_data.c.Password,user_data.c.Name,user_data.c.Plan,user_data.c.Hit_count_left,user_data.c.Updated_time)
results = connection.execute(query).fetchall()
connection.commit()
print(results)

user_activity = Table('User_Activity', metadata, autoload_with=engine)

# Print the column names
print(user_activity.columns.keys())

# # Print full table metadata
print(repr(metadata.tables['User_Activity']))

query = insert(user_activity) 
values_list = [{'UserID':'dhanush@gmail.com', 'Source':'Boston (BOS)', 'Destination':'New York (JFK)', 'S_Date':'2023/05/01', 'E_Date':'2023/05/15', 'Duration':'5', 'Budget':'2500' , 'TotalPeople':'4','Time_stamp':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
               {'UserID':'nishant@gmail.com', 'Source':'Boston (BOS)', 'Destination':'New York (JFK)', 'S_Date':'2023/05/01', 'E_Date':'2023/05/15', 'Duration':'5', 'Budget':'2500' , 'TotalPeople':'4', 'Time_stamp':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
               {'UserID':'shubham@gmail.com', 'Source':'Boston (BOS)', 'Destination':'San francisco (SFO)', 'S_Date':'2023/05/05', 'E_Date':'2023/05/15', 'Duration':'10', 'Budget':'3500' , 'TotalPeople':'2','Time_stamp':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
               {'UserID':'dhanush@gmail.com', 'Source':'New york (JFK)', 'Destination':'Boston (BOS)', 'S_Date':'2023/06/01', 'E_Date':'2023/06/15', 'Duration':'5', 'Budget':'2500' , 'TotalPeople':'4','Time_stamp':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
               ]

ResultProxy = connection.execute(query,values_list)
query=select(user_activity.c.UserID,user_activity.c.Source,user_activity.c.Destination,user_activity.c.S_Date,user_activity.c.E_Date,user_activity.c.Duration,user_activity.c.Budget,user_activity.c.TotalPeople,user_activity.c.Time_stamp)
results = connection.execute(query).fetchall()
connection.commit()
print(results)


plan = Table('plan', metadata, autoload_with=engine)

# Print the column names
print(plan.columns.keys())

# # Print full table metadata
print(repr(metadata.tables['plan']))

query = insert(plan) 
values_list = [{'plan_name':'Basic', 'api_limit':10},
               {'plan_name':'Standard', 'api_limit':25},
               {'plan_name':'Premium', 'api_limit':50}
               ]

ResultProxy = connection.execute(query,values_list)
query=select(plan.c.plan_name,plan.c.api_limit)
results = connection.execute(query).fetchall()
connection.commit()
print(results)


aoi = Table('AOI', metadata, autoload_with=engine)

# Print the column names
print(aoi.columns.keys())

# # Print full table metadata
print(repr(metadata.tables['AOI']))

query = insert(aoi) 
values_list = [{'UserID':'dhanush@gmail.com', 'Interest':'tourist attraction, hiking'},
               {'UserID':'nishant@gmail.com', 'Interest':'tourist attraction, hiking, food'},
               {'UserID':'shubham@gmail.com', 'Interest':'tourist attraction, hiking, museums'}
               ]

ResultProxy = connection.execute(query,values_list)
query=select(aoi.c.UserID,aoi.c.Interest)
results = connection.execute(query).fetchall()
connection.commit()
print(results)