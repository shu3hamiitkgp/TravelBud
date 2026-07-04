import numpy as np
import requests
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv
import json

load_dotenv()

#-------------------------------------------------------------------#
## Hotel Booking API
#-------------------------------------------------------------------#

def get_location_id(destination):
  url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"

  querystring = {"name": destination,"locale":"en-gb"}

  headers = {
    "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY_HOTEL'),
    "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
  }

  response = requests.request("GET", url, headers=headers, params=querystring)

  response = response.json()
  return response[1]['dest_id'], response[1]['dest_type']

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

#-------------------------------------------------------------------#
## Flight Booking API
#-------------------------------------------------------------------#


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



   


def get_final_cost(start_date_val, end_date_val, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val):

    # get hotel data
    start_date = start_date_val #str
    end_date = end_date_val #str
    num_days = num_days_val #int
    adults_number = adults_number_val #int
    num_rooms = num_rooms_val #str
    des_id, type_des= get_location_id(detination_name_val) #str
    df_sorted  = calculate_hotel_costs(start_date, end_date, num_days, adults_number, type_des, des_id, num_rooms)


    # get flight data
    date_pairs = create_date_pairs(start_date, end_date, num_days)
    flight_data = pd.DataFrame()
    
    for pair in date_pairs:
        result = get_flight_data(type_val, origin_val, destination_val, str(adults_number_val), pair[0], pair[1])
        flight_data = pd.concat([flight_data, result], ignore_index=True)

    # check if flight data is empty
    if flight_data.empty:
        # return only the hotel data
        return df_sorted.head(1)


    flight_data = flight_data.drop_duplicates()
    print(flight_data)
    # convert price column to float type
    flight_data['Price'] = flight_data['Price'].str.replace('$', '').astype(float)

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
    if merged_df['Total_cost'].min() <= budget_val:
        return merged_df.loc[merged_df['Total_cost'].idxmin()]
    else:
        print('The budget is not enough but here is the best we can do')
        return merged_df.head(1)


# example usage
df = get_final_cost('2023-04-30', '2023-05-10', 2, 1, '1', 'Orlando', 'Best', 'JFK', 'ORL', 1100)
print(df)

