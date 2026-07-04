import schema
from fastapi import FastAPI,Depends,Response,status
import os
import pandas as pd
from passlib.context import CryptContext
import access_token
from fastapi.security import OAuth2PasswordRequestForm
import common_utils as cu
import boto3
import DB_Connect as database
import requests
from pydantic import BaseModel
from dotenv import load_dotenv
import googlemaps
from itertools import combinations
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, TEXT, Identity, inspect, select, update,insert
from sqlalchemy_utils import database_exists, create_database
import oauth2
from typing import Union
from fpdf import FPDF
import openai
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
from fastapi.responses import JSONResponse
from datetime import datetime

load_dotenv()

cwd = os.getcwd()
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()
    
db = database.DB()

class MyPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'TravelBud', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page %s' % self.page_no(), 0, 0, 'C')

    def create_page(self, text):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, text)
        self.ln()

@app.post('/login')
async def login(login_data: OAuth2PasswordRequestForm = Depends()):
    userTable = db.getTable('User_Details')
    result = db.selectWhere(userTable, 'UserID', str(login_data.username))
    rows = [dict(row) for row in result]
    user = pd.DataFrame(rows)
    if len(user) == 0:
        data = {"message": "User not found", "status_code": "404"}
    else:
        pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if pwd_cxt.verify(login_data.password, user['Password'][0]):
            print("password verified")
            data = {'message': 'Username verified successfully', 'status_code': '200'}
            accessToken = access_token.create_access_token(data={"sub": str(user['UserID'][0])})
            data = {'message': "Success",'access_token':accessToken,'service_plan': user['Plan'][0],'status_code': '200'}
        else:
            data = {'message': 'Password is incorrect','status_code': '401'}
    return data

@app.post('/signup')
async def signup(user_data: schema.UserData):
    userTable = db.getTable('User_Details')
    user = db.selectWhere(userTable, 'UserID', user_data.Username)
    for u in user:
        data = {"message": "This email already exists", "status_code": "404"}
        # return data
        return JSONResponse(content=data, status_code=404)

    pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_cxt.hash(user_data.Password)
    planTable = db.getTable('plan')
    planResult = db.selectWhere(planTable, 'plan_name', user_data.Plan)
    planRows = [dict(row) for row in planResult]
    plan = pd.DataFrame(planRows)
    db.insertRow(userTable, [{'UserID': user_data.Username, 'Password': hashed_password, 'Name': user_data.Name, 'Plan': user_data.Plan, 'Hit_count_left': int(plan['api_limit'][0]), 'Updated_time': datetime.now()}])
    for interest in user_data.AOI:
        db.insertRow(db.getTable('AOI'), [{'UserID': user_data.Username, 'Interest': interest}])
    data = {"message": "User created successfully", "status_code": "200"}
    # return data
    return JSONResponse(content=data, status_code=200)

@app.post('/forgot_password')
async def forgot_password(user_data: schema.ForgotPassword):
    userTable = db.getTable('User_Details')
    result = db.selectWhere(userTable, 'UserID', str(user_data.Username))
    rows = [dict(row) for row in result]
    user = pd.DataFrame(rows)
    if len(user) == 0:
        data = {"message": "User not found", 'status_code': "404"}
    else:
        pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_cxt.hash(user_data.Password)
        db.updateRow(userTable,'Password', hashed_password, 'UserID',user_data.Username)
        data = {"message": "Password updated successfully", 'status_code': "200"}
    return data

@app.post('/update_User')
async def update_User(user_data: schema.UpdateData, getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):
    userTable = db.getTable('User_Details')
    result = db.selectWhere(userTable, 'UserID', str(user_data.Username))
    rows = [dict(row) for row in result]
    user = pd.DataFrame(rows)
    if len(user) == 0:
        data = {"message": "User not found", "status_code": "404"}
    else:
        if user['Plan'][0] != user_data.Plan:
            planTable = db.getTable('plan')
            planResult = db.selectWhere(planTable, 'plan_name', user_data.Plan)
            planRows = [dict(row) for row in planResult]
            plan = pd.DataFrame(planRows)
            db.updateRow(userTable, 'Hit_count_left', int(plan['api_limit'][0]), 'UserID', user_data.Username)
            db.updateRow(userTable, 'Updated_time', datetime.now(), 'UserID', user_data.Username)
            db.updateRow(userTable, 'Plan', user_data.Plan, 'UserID', user_data.Username)

        db.deleteByValue(db.getTable('AOI'), 'UserID', user_data.Username)
        for interest in user_data.AOI:
            db.insertRow(db.getTable('AOI'), [{'UserID': user_data.Username, 'Interest': interest}])
        data = {"message": "User updated successfully", "status_code": "200"}
    return data

def create_date_pairs(start_date, end_date, num_days):

    date_pairs = []
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    while current_date <= end_date:
        pair_end_date = current_date + timedelta(days=num_days-1)
        if pair_end_date > end_date:
            pair_end_date = end_date
        date_pairs.append((current_date.strftime('%Y-%m-%d'), pair_end_date.strftime('%Y-%m-%d')))
        current_date += timedelta(days=1)  

    return date_pairs[:-num_days+1]  # remove the last pair if it's incomplete

def get_hotel_cost(checkin_date, checkout_date, adults_number, type_des, id, rooms_cnt):

    url = "https://booking-com.p.rapidapi.com/v1/hotels/search"

    querystring = {
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults_number": adults_number,
        "dest_type": type_des,
        "units": "metric",
        "order_by": "review_score", #sorting by review score and then finding the lowest price
        "dest_id": id,
        "filter_by_currency": "USD",
        "locale": "en-gb",
        "room_number": rooms_cnt,
        "page_number": "0",
        "include_adjacency": "true"
    }

    headers = {
                "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY_HOTEL'),
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"

    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    result = response.json()
    return result

def calculate_hotel_costs(start_date, end_date, num_days, adults_number, type_des, id, rooms_cnt):

    date_pairs = create_date_pairs(start_date, end_date, num_days)
    hotel_costs = []
    df_list = []

    for pair in date_pairs:
        checkin_date = datetime.strptime(pair[0], '%Y-%m-%d')
        checkout_date = datetime.strptime(pair[1], '%Y-%m-%d')
        response = get_hotel_cost(checkin_date.strftime('%Y-%m-%d'), checkout_date.strftime('%Y-%m-%d'), adults_number, type_des, id, rooms_cnt)
        hotel_names = []
        prices = []
        for val in response['result']:
            hotel_names.append(val['hotel_name'])
            prices.append(val['composite_price_breakdown']['all_inclusive_amount']['value'])
        hotel_names, prices = zip(*sorted(zip(hotel_names, prices), key=lambda x: x[1]))
        hotel_cost = {
            'start_date': checkin_date.strftime('%Y-%m-%d'),
            'end_date': checkout_date.strftime('%Y-%m-%d'),
            'hotel_names': list(hotel_names),
            'prices': list(prices)
        }
        hotel_costs.append(hotel_cost)

        for cost in hotel_costs:
            start_date = cost['start_date']
            end_date = cost['end_date']
            hotel_names = cost['hotel_names']
            prices = cost['prices']
            df_temp = pd.DataFrame({
                'start_date': [start_date]*len(hotel_names),
                'end_date': [end_date]*len(hotel_names),
                'hotel_name': hotel_names,
                'price': prices
            })
            df_list.append(df_temp)

        df = pd.concat(df_list, ignore_index=True)
        df_sorted = df.sort_values(by='price', ascending=True).reset_index(drop=True)
    return df_sorted


def get_flight_data(type_val, origin_val, destination_val, adults_number, start_date, end_date):

    price_lst = []
    airline_lst = []

    url = "https://skyscanner44.p.rapidapi.com/search"

    querystring = {"adults":adults_number ,"origin": origin_val,"destination": destination_val ,"departureDate": start_date,"returnDate": end_date ,"currency":"USD"}
    headers = {
        "content-type": "application/octet-stream",
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY_AIRLINE'),
        "X-RapidAPI-Host": "skyscanner44.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring).json()

    # print(response)

    if 'itineraries' not in response:
        return pd.DataFrame({'Airline': [], 'Price': [], 'Start Date': [], 'End Date': []})

    if type_val == 'Best':
        type_val = 0

    elif type_val == 'Cheapest':
        type_val = 1

    elif type_val == 'Fastest':
        type_val = 2

    elif type_val == 'Direct':
        type_val = 3

    else:
        return 'Invalid type selected'

    if len(response['itineraries']['buckets']) == 0:
      return

    for val in (response['itineraries']['buckets'][type_val]['items']):
        price_lst.append(val['price']['formatted'])
        airline_lst.append(val['legs'][1]['segments'][0]['operatingCarrier']['name'])


    return pd.DataFrame({'Airline': airline_lst, 'Price': price_lst, 'Start Date': [start_date]* len(price_lst), 'End Date': [end_date] * len(price_lst)})

def translate_text(text, dest_lang):
    if dest_lang == 'Spanish':
        dest_lang = 'es_XX'
    if dest_lang == 'Hindi':
        dest_lang = 'hi_IN'

    model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
    tokenizer = MBart50TokenizerFast.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
    tokenizer.src_lang = "en_XX"
    tokenizer.tgt_lang = dest_lang
    
    # Split input text into smaller chunks of length less than or equal to 1024
    chunk_size = 1024
    text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    # Translate each text chunk separately
    translated_chunks = []
    for chunk in text_chunks:
        encoded_chunk = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=1024)
        generated_tokens = model.generate(
            input_ids=encoded_chunk.input_ids,
            attention_mask=encoded_chunk.attention_mask,
            forced_bos_token_id=tokenizer.lang_code_to_id[dest_lang],
            max_length=1024,
            num_beams=4,
            early_stopping=True,
        )
        translated_chunk = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        translated_chunks.append(translated_chunk)

    # Concatenate the translated output of each chunk to obtain the final translated text
    translated_text = ''.join(translated_chunks)
    return translated_text

def create_itinerary(User_name, start_date, end_date, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, hotel_name, price, airline, flight_price, total_cost, locations, pairing):
    itinerary = """Create a detailed itinerary of 500 words for a user based on the following info don't deviate from the given Info start with customised greeting based on the user name and end with terms and conditions
    Details:
    - User Name: {User_name}
    - Start Date: {start_date}
    - End Date: {end_date}
    - Number of Days: {num_days_val}
    - Number of Adults: {adults_number_val}
    - Number of Rooms: {num_rooms_val}
    - Destination: {detination_name_val}
    - Type: {type_val}
    - Origin: {origin_val}
    - Destination: {destination_val}
    - Budget: {budget_val}
    Hotel:
    - Name: {hotel_name}
    - Hotel Price: {price}
    Flight:
    - Airline: {airline}
    - Airline Price: {flight_price}
    Total Cost: {total_cost}
    Locations:
    {locations}
    {pairing}
    If there is any left-out location include it on the remaining days and add terms and conditions at the end""".format(User_name = User_name, start_date = start_date, end_date = end_date, num_days_val = num_days_val, adults_number_val = adults_number_val, num_rooms_val = num_rooms_val, detination_name_val = detination_name_val, type_val = type_val, origin_val = origin_val, destination_val = destination_val, budget_val = budget_val, hotel_name = hotel_name, price = price, airline = airline, flight_price = flight_price, total_cost = total_cost, locations = locations, pairing = pairing)

    return itinerary

def chat(inp, message_history, role="user"):

    """Question to be asked to the chatgpt api
    Args:
        inp (str): Input from the user
        message_history (list): Message history
        role (str): Role of the user
    Returns:
        reply (str): Reply from the chatgpt api
    """

    # Append the input message to the message history
    message_history.append({"role": role, "content": f"{inp}"})
    openai.api_key = os.environ.get('OPENAI_API_KEY')


    # Generate a chat response using the OpenAI API
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_history,
        temperature=0.15,
    )

    # Grab just the text from the API completion response
    reply_content = completion.choices[0].message.content

    # Append the generated response to the message history
    message_history.append({"role": "assistant", "content": f"{reply_content}"})

    # Return the generated response.
    return reply_content

def create_connection():
    """Create a connection to S3 bucket
    Returns:
        s3client: S3 client object
    """
    s3client = boto3.client('s3', region_name= "us-east-1", aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
    return s3client

@app.post('/GetTopAttractions')
async def get_top_attractions(data: schema.top_attractions, getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):

    API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    attractions_lst = []

    # define parameters for API request
    radius = "10000"  # in meters
    # types = 'tourist_attraction|amusement_park|park|point_of_interest|establishment'

    # build API request URL
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={data.city}&radius={radius}&types={data.types}&key={API_KEY}"

    # send API request and get JSON response
    response = requests.get(url).json()

    # get top 10 attractions by rating
    attractions = sorted(response["results"], key=lambda x: x.get("rating", 0), reverse=True)[:10]

    # print names and addresses of top 10 attractions
    for attraction in attractions:
        attractions_lst.append(attraction["name"])

    # check if the response has at least 10 attractions
    if len(attraction["name"]) < 10:
        
        default_types = 'tourist_attraction|amusement_park|park|point_of_interest|establishment'

        # build API request URL
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={data.city}&radius={radius}&types={default_types}&key={API_KEY}"
        # send API request and get JSON response
        response = requests.get(url).json()
        # get top 10 attractions by rating
        attractions = sorted(response["results"], key=lambda x: x.get("rating", 0), reverse=True)[:10]
        # print names and addresses of top 10 attractions
        for attraction in attractions:
            attractions_lst.append(attraction["name"])

    response_data = {'data': attractions_lst,
            'status_code': '200'}

    return response_data

@app.post('/FindOptimalPairs')
async def find_optimal_pairs(data: schema.optimal_pairs, getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):

    gmaps = googlemaps.Client(key= os.environ.get('GOOGLE_MAPS_API_KEY'))

    location_pairs = list(combinations(data.locations, 2))

    distances = {}
    for pair in location_pairs:
        distance = gmaps.distance_matrix(pair[0], pair[1])['rows'][0]['elements'][0]['distance']['value'] / 1000
        distances[pair] = distance

    sorted_distances = sorted(distances.items(), key=lambda x: x[1])

    visited_locations = set()
    optimal_pairs = []

    for pair, distance in sorted_distances:
        if pair[0] not in visited_locations and pair[1] not in visited_locations:
            optimal_pairs.append((pair, distance))
            visited_locations.add(pair[0])
            visited_locations.add(pair[1])

    left_out_locations = set(data.locations) - visited_locations

    result_str = ""
    day = 1
    for pair, distance in optimal_pairs:
        result_str += f"Day {day}: {pair[0]} and {pair[1]}: {distance} km\n"
        day += 1

    if left_out_locations:
        result_str += f"Day {day}: Left out location: {' '.join(left_out_locations)}"

    response_data = {'data': result_str,
            'status_code': '200'}
    
    return response_data

@app.post('/GetFinalCost')
async def get_final_cost(data: schema.final_cost, getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):

    # get hotel data
    start_date = data.start_date_val #str
    end_date = data.end_date_val #str
    num_days = data.num_days_val #int
    adults_number = data.adults_number_val #int
    num_rooms = data.num_rooms_val #str
    df_sorted  = calculate_hotel_costs(start_date, end_date, num_days, adults_number, data.type_des, data.des_id, num_rooms)


    # get flight data
    date_pairs = create_date_pairs(start_date, end_date, num_days)
    flight_data = pd.DataFrame()
    
    for pair in date_pairs:
        result = get_flight_data(data.type_val, data.origin_val, data.destination_val, str(data.adults_number_val), pair[0], pair[1])
        flight_data = pd.concat([flight_data, result], ignore_index=True)

    # check if flight data is empty
    if flight_data.empty:
        # return only the hotel data
        response_data = {'data': df_sorted.head(1),
            'status_code': '200'}
        return response_data

    flight_data = flight_data.drop_duplicates()
    # print(flight_data)

    flight_data['Price'] = [str(x).replace('$', '') for x in flight_data['Price']]
    flight_data['Price'] = [str(x).replace(',', '') for x in flight_data['Price']]
    flight_data['Price'] = [float(x) for x in flight_data['Price']]

    # convert price column to float type
    # flight_data['Price'] = flight_data['Price'].str.replace('$', '').astype(float)
    # flight_data['Price'] = flight_data['Price'].str.replace(',', '').astype(float)

    # group by start and end dates and get the row with lowest price for each group
    flight_data = flight_data.sort_values('Price').groupby(['Start Date', 'End Date'], as_index=False).first()

    # reset index
    flight_data = flight_data.reset_index(drop=True)

    # output result as list of dictionaries
    result = flight_data.to_dict(orient='records')
    result = pd.DataFrame(result)

    merged_df = pd.merge(df_sorted, result, left_on='start_date', right_on = 'Start Date', how='inner')
    merged_df['Total_cost'] = merged_df['price'] + merged_df['Price']
    merged_df.sort_values(by = 'Total_cost')

    # get the lowest cost and if matches the budget, return the dataframe else return the first row with message stating that the budget is not enough but here is the best we can do
    if merged_df['Total_cost'].min() <= data.budget_val:
        # return merged_df.loc[merged_df['Total_cost'].idxmin()]
        response_data = {'data': merged_df.loc[merged_df['Total_cost'].idxmin()],
            'status_code': '200'}
    else:
        # print('The budget is not enough but here is the best we can do')
        # return merged_df.head(1)
        response_data = {'data': merged_df.loc[merged_df['Total_cost'].idxmin()],
            'status_code': '200'}


    # response_data = {'data': df_sorted,
    #         'status_code': '200'}
    
    return response_data
    # return df_sorted


@app.get("/get_useract_data")
async def useract_data(getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):
    # config={'DB_USER_NAME':'postgres',
    #     'DB_PASSWORD':'shubh',
    #     'DB_ADDRESS':'localhost',
    #     'DB_NAME':'final_project'}
    engine=create_engine('postgresql://'+str(os.environ.get('DB_USER_NAME'))+':'+str(os.environ.get('DB_PASSWORD'))+'@'+str(os.environ.get('DB_HOST'))+':5432/'+str(os.environ.get('DB_NAME')))
    connection = engine.connect()
    metadata = MetaData()
    try:
        user_data = Table('User_Details', metadata, autoload_with=engine)
        query=select(user_data.c.UserID,user_data.c.Password,user_data.c.Name,user_data.c.Plan,user_data.c.Hit_count_left,user_data.c.Updated_time)
        results = connection.execute(query).fetchall()
        user_data=pd.DataFrame(results,columns=['UserID','Password','Name','Plan','Hit_count_left','Updated_time'])
        df_user_data=user_data.to_dict(orient='records')
        user_activity = Table('User_Activity', metadata, autoload_with=engine)
        query=select(user_activity.c.UserID,user_activity.c.Source,user_activity.c.Destination,user_activity.c.S_Date,user_activity.c.E_Date,user_activity.c.Duration,user_activity.c.Budget,user_activity.c.TotalPeople,user_activity.c.Time_stamp)
        results = connection.execute(query).fetchall()
        user_activity=pd.DataFrame(results,columns=['UserID','Source','Destination','S_Date','E_Date','Duration','Budget','TotalPeople','Time_stamp'])
        df_user_activity=user_activity.to_dict(orient='records')
        plan = Table('plan', metadata, autoload_with=engine)
        query=select(plan.c.plan_name,plan.c.api_limit)
        results = connection.execute(query).fetchall()
        plan=pd.DataFrame(results,columns=['plan_name','api_limit'])
        df_plan=plan.to_dict(orient='records')
        aoi = Table('AOI', metadata, autoload_with=engine)
        query=select(aoi.c.UserID,aoi.c.Interest)
        results = connection.execute(query).fetchall()
        aoi=pd.DataFrame(results,columns=['UserID','Interest'])
        df_aoi=plan.to_dict(orient='records')
        return {'user_data':df_user_data,'user_activity':df_user_activity,'plan':df_plan,'aoi':df_aoi}
    except:
        return {'data':'No data found'}
    
@app.post("/get_current_username")
async def get_username(getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):
    return {'username': getCurrentUser.username}


@app.post("/get_current_name")
async def get_username(getCurrentName: schema.currentName):
    userTable = db.getTable('User_Details')
    result = db.selectWhere(userTable, 'UserID', str(getCurrentName.Username))
    rows = [dict(row) for row in result]
    user = pd.DataFrame(rows)
    if len(user) == 0:
        return {'data':'User does not exist','status':400}
    else:
        hitCount =  int(user['Hit_count_left'][0])
        name = str(user['Name'][0])
        return {'Name': name, 'Hit_count': hitCount, 'status':200}

@app.post('/user_api_status')
async def get_user_data(api_details: schema.api_detail_fetch,getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):
    # database_file_name = "assignment_01.db"
    # database_file_path = os.path.join(project_dir, os.path.join('data/',database_file_name))
    # db = sqlite3.connect(database_file_path)
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE if not exists user_activity (username,service_plan,api_limit,date,api_name,hit_count)''')
    cursor.execute('SELECT * FROM user_activity WHERE username =? ORDER BY date DESC LIMIT 1',(getCurrentUser.username,))
    result = cursor.fetchone()
    username=getCurrentUser.username
    api_limit=pd.read_sql_query('Select api_limit from Users where username="{}"'.format(username),db).api_limit.item()
    date = datetime.utcnow()
    service_plan=pd.read_sql_query('Select service_plan from Users where username="{}"'.format(username),db).service_plan.item()
    api_name=api_details.api_name 
    if not result:
        hit_count = 1
        cursor.execute('INSERT INTO user_activity VALUES (?,?,?,?,?,?)', (username,service_plan,api_limit,date,api_name,hit_count))
        db.commit()
    else:
        last_date = datetime.strptime(result[3], '%Y-%m-%d %H:%M:%S.%f')
        time_diff = datetime.utcnow() - last_date
        if time_diff <= timedelta(hours=1):
            if result[5]<api_limit:
                hit_count = result[5] + 1
                cursor.execute('INSERT INTO user_activity VALUES (?,?,?,?,?,?)', (username,service_plan,api_limit,date,api_name,hit_count))
                db.commit()
            else:
                db.commit()
                db.close() 
                return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        else:
            hit_count = 1
            cursor.execute('INSERT INTO user_activity VALUES (?,?,?,?,?,?)', (username,service_plan,api_limit,date,api_name,hit_count))
            db.commit()

@app.post('/CreatePDF')
async def create_pdf(data: schema.create_pdf):

    try:
        prompt = create_itinerary(data.User_name, data.start_date, data.end_date, data.num_days_val, data.adults_number_val, data.num_rooms_val, data.detination_name_val, data.type_val, data.origin_val, data.destination_val, data.budget_val, data.hotel_name, data.price, data.airline, data.flight_price, data.total_cost, data.locations, data.pairing)
        message_history = []
        gpt_response = chat(prompt, message_history)

        if data.language == 'English':
            pass
        if data.language == "Spanish":
            gpt_response = translate_text(gpt_response, 'Spanish')

        if data.language == "Hindi":
            gpt_response = translate_text(gpt_response, 'Hindi')

        pdf = MyPDF()
        pdf.add_page()
        text = gpt_response
        pdf.create_page(text)
        pdf.output(data.user_email + "_itinerary.pdf")

        response_data = {'message': 'Generated PDF',
            'status_code': '200'}

        return response_data
    
    except Exception as e:
        response = {'status_code': '500'}
        return response

# @app.post('/user_api_status')
# async def get_user_data(api_details: schema.api_detail_fetch,getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):
#     # database_file_name = "assignment_01.db"
#     # database_file_path = os.path.join(project_dir, os.path.join('data/',database_file_name))
#     # db = sqlite3.connect(database_file_path)
#     cursor = db.cursor()
#     cursor.execute('''CREATE TABLE if not exists user_activity (username,service_plan,api_limit,date,api_name,hit_count)''')
#     cursor.execute('SELECT * FROM user_activity WHERE username =? ORDER BY date DESC LIMIT 1',(getCurrentUser.username,))
#     result = cursor.fetchone()
#     username=getCurrentUser.username
#     api_limit=pd.read_sql_query('Select api_limit from Users where username="{}"'.format(username),db).api_limit.item()
#     date = datetime.utcnow()
#     service_plan=pd.read_sql_query('Select service_plan from Users where username="{}"'.format(username),db).service_plan.item()
#     api_name=api_details.api_name 
#     if not result:
#         hit_count = 1
#         cursor.execute('INSERT INTO user_activity VALUES (?,?,?,?,?,?)', (username,service_plan,api_limit,date,api_name,hit_count))
#         db.commit()
#     else:
#         last_date = datetime.strptime(result[3], '%Y-%m-%d %H:%M:%S.%f')
#         time_diff = datetime.utcnow() - last_date
#         if time_diff <= timedelta(hours=1):
#             if result[5]<api_limit:
#                 hit_count = result[5] + 1
#                 cursor.execute('INSERT INTO user_activity VALUES (?,?,?,?,?,?)', (username,service_plan,api_limit,date,api_name,hit_count))
#                 db.commit()
#             else:
#                 db.commit()
#                 db.close() 
#                 return Response(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
#         else:
#             hit_count = 1
#             cursor.execute('INSERT INTO user_activity VALUES (?,?,?,?,?,?)', (username,service_plan,api_limit,date,api_name,hit_count))
#             db.commit()


@app.post('/submit')
async def submit(user_activity: schema.user_activity, getCurrentUser: schema.TokenData = Depends(oauth2.get_current_user)):
    #userActivityTable = db.getTable('user_activity')
    userActivityTable = db.getTable('User_Activity')
    
    userTable = db.getTable('User_Details')
    result = db.selectWhere(userTable, 'UserID', str(getCurrentUser.username))
    rows = [dict(row) for row in result]
    user = pd.DataFrame(rows)
    current_timestamp = datetime.utcnow()
    if len(user) == 0:
        return {'data':'User does not exist','status':400}
    else:
        if int(user['Hit_count_left'][0]) == 0:
            return {'data':'User has exhausted the API limit','status':400}
        else:
            updated_hit_count = int(user['Hit_count_left'][0]) - 1
            db.updateRow(userTable,'Hit_count_left', updated_hit_count, 'UserID',user_activity.UserID)
            db.insertRow(userActivityTable, [{"UserID":getCurrentUser.username, "Source": user_activity.Source, "Destination": user_activity.Destination, "S_Date": user_activity.S_Date, "E_Date": user_activity.E_Date, "Duration": user_activity.Duration, "TotalPeople": user_activity.TotalPeople, "Budget": user_activity.Budget, "Time_stamp": current_timestamp}])
            return {'data':'Submitted successfully','status':200}