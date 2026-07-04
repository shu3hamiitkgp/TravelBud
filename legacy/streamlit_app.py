import streamlit as st
import requests
from backend import google_maps, top_10_places, common_utils
from dotenv import load_dotenv
import os
import airportsdata
from datetime import datetime,timedelta
import pandas as pd
from jose import JWTError, jwt
# import seaborn as sns
# import matplotlib.pyplot as plt
# import numpy as np


load_dotenv()

API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

ACCESS_TOKEN = st.session_state.get("token", None)
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}


# Define background images
# home_bg = ""
# page_bg = ""
# def decode_token(token):
#     try:
        
#         res = requests.get(
#         'http://localhost:8000/get_current_username', headers=headers)
        
#         return res["username"]
#     except:
#         return None

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        return None    
    
# Set page config
# st.set_page_config(page_title="TravelBud", page_icon=":earth_americas:")

is_logged_in = False

if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

def get_top_attractions(destination, interests):
    
    data = {
        "city": destination,
        "types": interests
    }

    res = requests.post(
        'http://localhost:8000/GetTopAttractions', json=data,headers=headers)
    
    response = res.json()

    if response["status_code"] == 200 or response["status_code"] == '200':
        return response

def find_optimal_pairs(selected_places):

    try:
        data = {
                "locations": selected_places
            }

        res = requests.post(
            'http://localhost:8000/FindOptimalPairs', json=data,headers=headers)
                    
        response = res.json()

        if response["status_code"] == '200':
            return response
        
    except Exception as e:
        response = {'status_code': '500'}
        return response

def get_location_id(destination):

    url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"

    querystring = {"name": destination,"locale":"en-gb"}

    headers_hotel = {
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY_HOTEL'),
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }
    print('111111')
    response = requests.request("GET", url, headers=headers_hotel, params=querystring)
    print(response)
    response = response.json()
    print(response[1]['dest_id'])
    return response[1]['dest_id'], response[1]['dest_type']

def create_pdf(num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, start_date, end_date, hotel_name, price, flight_start_date, flight_end_date, airline, flight_price, total_cost, User_name, pairing, locations, language, user_email):

    data = {
            "num_days_val": num_days_val,
            "adults_number_val": adults_number_val,
            "num_rooms_val": num_rooms_val,
            "detination_name_val": detination_name_val,
            "type_val": type_val,
            "origin_val": origin_val,
            "destination_val": destination_val,
            "budget_val": budget_val,
            "start_date": start_date,
            "end_date": end_date,
            "hotel_name": hotel_name,
            "price": price,
            "flight_start_date": flight_start_date,
            "flight_end_date": flight_end_date,
            "airline": airline,
            "flight_price": flight_price,
            "total_cost": total_cost,
            "User_name": User_name,
            "pairing": pairing,
            "locations": locations,
            "language": language,
            "user_email": user_email
        }

    res = requests.post(
        'http://localhost:8000/CreatePDF', json=data,headers=headers)
                
    response = res.json()

    return response

def get_final_cost(start_date_val, end_date_val, num_days_val, adults_number_val, num_rooms_val, des_id, type_des, type_val, origin_val, destination_val, budget_val):

    data = {
        "start_date_val": start_date_val,
        "end_date_val": end_date_val,
        "num_days_val": num_days_val,
        "adults_number_val": adults_number_val,
        "num_rooms_val": num_rooms_val,
        "des_id": des_id,
        "type_des": type_des,
        "type_val": type_val,
        "origin_val": origin_val,
        "destination_val": destination_val,
        "budget_val": budget_val
    }

    res = requests.post(
        'http://localhost:8000/GetFinalCost', json=data,headers=headers)
    
    response = res.json()

    if response["status_code"] == 200 or response["status_code"] == '200':
        return response

# Helper function to format the selectbox options for places
def format_select_option(pair):
    return f"{pair[0]} ({pair[1]})"

def login():
    # Set background image
    # st.markdown(f'<style>body{{background-image: url({page_bg}); background-size: cover;}}</style>', unsafe_allow_html=True)
    global is_logged_in
    st.title('TravelBud')
    st.subheader('Welcome to TravelBud! Please Login to proceed.')
    # Get user input
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    # Login button
    if st.button("Login"):
        # Check if login is valid
        data = {
                "grant_type": "password",
                "username": email,
                "password": password
                }
        loginResult = requests.post('http://localhost:8000/login',data=data)
        if int(loginResult.json()['status_code']) == 200:
            os.environ["access_token"] = loginResult.json()["access_token"]
            access_token=loginResult.json()["access_token"]
            
            with open(".env", "r") as f:
                lines = f.readlines()

            # Find the line that contains the access token
            for i, line in enumerate(lines):
                if line.startswith("access_token="):
                    # Replace the access token with the new value
                    lines[i] = "access_token=" + loginResult.json()['access_token'] + "\n"
                    break

            # Write the modified lines back to the file
            with open(".env", "w") as f:
                f.writelines(lines)
            st.success("Logged in!")
            
            st.session_state['is_logged_in'] = True
            # print(access_token)
            return access_token
            
        else:
            st.error("Incorrect email or password")

    # if st.button("Forgot Password"):
    #     st.info("Enter your email address and password over here to reset your password")

    #     # Get user input
    #     yourEmail = st.text_input("Your Email")
    #     newPassword = st.text_input("New Password", type="password")
    #     confirmNewPassword = st.text_input("Confirm New Password", type="password")

        # Reset Password button
        

def forget_password():
    st.info("Enter your email address and password over here to reset your password")
    yourEmail = st.text_input("Your Email")
    newPassword = st.text_input("New Password", type="password")
    confirmNewPassword = st.text_input("Confirm New Password", type="password")
    # password_regex = "^[a-zA-Z0-9]{8,}$"
    # username = st.text_input("Enter username")
    # password = st.text_input(
    #     "Enter new password", type="password"
    # )  # Validate credit card
    # if not re.match(password_regex, password):
    #     st.error(
    #         "Password must be at least 8 characters long and can only contain alphanumeric characters."
    #     )
    # if st.button("Update Password"):
    #     url = f"{PREFIX}/forget-password?username={username}&password={password}"
    #     response = requests.put(url)
    #     if response.status_code == 200:
    #         st.write("Password Updated Successfully")
    #     elif response.status_code == 404:
    #         st.error("User not found.")
    #     else:
    #         st.error("Error updating password.")
    if st.button("Reset Password"):
            # Check if email is valid
            if newPassword == confirmNewPassword:
                resetResult = requests.post('http://localhost:8000/forgot_password',json={"Username": yourEmail, "Password": newPassword})
                if int(resetResult.json()['status_code'])==200:
                    st.success("Password reset successfully!")
                else:
                    st.error("Email address not found")
            else:
                st.error("Passwords do not match")

def signup():
    # Set background image
    # st.markdown(f'<style>body{{background-image: url({page_bg}); background-size: cover;}}</style>', unsafe_allow_html=True)

    st.subheader('Signup')
    # Get user input
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    AOI = []

    # Display a multiselect for the user to choose the place types
    selected_place_types = st.multiselect('Select your interests', google_maps.get_place_types())

    # Display the user's selection
    if selected_place_types:
        st.info("You selected: " + ", ".join(selected_place_types))

    # Join the selected types with the '|' separator
    types_str = '|'.join(selected_place_types)
    AOI.append(selected_place_types)

    # Define the plans as a dictionary
    plans = {
        "Basic": "10",
        "Standard": "25",
        "Premium": "50"
    }

    # Create a radio button group to display the plans
    selected_plan = st.radio("Select a plan", list(plans.keys()))

    # Display the selected plan's details
    st.info(f"You have selected the {selected_plan} plan. With the {selected_plan} plan, you can make {plans[selected_plan]} requests")


    # Signup button
    if st.button("Create Account"):
        # Check if password matches
        if password != confirm_password:
            st.error("Passwords do not match")
        else:
            signupResult = requests.post('http://localhost:8000/signup', json={"Username": email, "Password": password, "Name": name, "Plan": selected_plan, "AOI":AOI[0]})
            if int(signupResult.json()['status_code'])==200:
                st.success("Signed up!")
            else:
                st.error("Error signing up")

def home_page():
    # Set background image
    # st.markdown(f'<style>body{{background-image: url({home_bg}); background-size: cover;}}</style>', unsafe_allow_html=True)
    st.markdown("# TravelBud")

    # Create a menu with the options
    # menu = ["Home", "Login", "Signup"]
    # choice = st.sidebar.selectbox("Select an option", menu)

    # if choice == "Login":
        # login()
    # elif choice == "Signup":
        # signup()


def plan_my_trip_page():
    # Set background image
    # st.markdown(f'<style>body{{background-image: url({page_bg}); background-size: cover;}}</style>', unsafe_allow_html=True)
    
    st.markdown("# TravelBud")
    st.subheader('Plan My Trip')
    # st.sidebar.markdown("# Page 2 ❄️")
    st.sidebar.button("Logout")

    # Loading airport data
    airports = airportsdata.load('IATA')

    # Extract city names and corresponding IATA codes
    city_iata_pairs = [(data['city'], code) for code, data in airports.items()]

    # Selectbox for city selection
    source = st.selectbox("Select a source city", options=["Select"]+[format_select_option(p) for p in city_iata_pairs])

    # if source != "Select":
    # Remove the selected source city from destination options
    destination_options = [format_select_option(p) for p in city_iata_pairs if p[0] != source.split(" (")[0]]
    destination = st.selectbox("Select a destination city", options=["Select"]+destination_options)

    # destination = st.selectbox("Select a destination city", options=[format_option(p) for p in city_iata_pairs])

    if source != "Select" and destination != "Select":
        # Extract the selected city and IATA code
        # city, iata = source.split(" (")
        source_iata = source.split(" (")[1][:-1]
        # city, iata = destination.split(" (")
        destination_iata = destination.split(" (")[1][:-1]    

        # st.write(f" {source_iata} and {destination_iata}")

    # User Inputs
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    num_days = st.number_input('Enter the number of days for your trip', min_value=1, max_value=365, step=1)
    num_people = st.number_input("Enter the number of people", value=1, min_value=1)

    # define default number of rooms
    num_rooms = 1

    if num_people > 1:
        num_rooms = st.number_input('Enter the number of rooms', value=1, min_value=1)

    type_val = st.radio("Select flight type",('Best', 'Cheapest', 'Fastest', 'Direct'))

    # Budget Slider
    budget = st.slider("Budget", min_value=0, max_value=10000, step=100)

    interests = 'tourist_attraction|amusement_park|park|point_of_interest|establishment'


    if destination != "Select":

        res = get_top_attractions(destination.split(" (")[0], interests)

        selected_places = st.multiselect('Select the places', res["data"])
        # Displaying the user's selection
        if selected_places:
            st.info("You selected: " + ", ".join(selected_places))

    language = st.selectbox("Select a language", options = ['English','Spanish','Hindi'])

    if st.button("Submit"):
        dataSubmit = {"Source": source, "Destination": destination, "S_Date": start_date.strftime('%Y-%m-%d'), "E_Date": end_date.strftime('%Y-%m-%d'), "Duration": num_days, "TotalPeople": num_people, "Budget": budget}
        responseSubmit=requests.post('http://localhost:8000/submit', json=dataSubmit,headers=headers)
        # st.write(responseSubmit.json()['data'])
            
        with st.spinner('Hold on tight, we\'re cooking up the perfect adventure for you...'):

            if end_date < start_date:
                st.error("Error: End date should be greater than the start date.")
            elif (end_date - start_date).days < num_days:
                st.error("Error: Number of days should be less than the duration of the trip.")
            else:
                for i in range(len(selected_places)):
                    selected_places[i] += ' ' + destination.split(" (")[0]

                res_optimal_pairs = find_optimal_pairs(selected_places)

                if res_optimal_pairs["status_code"] == '500':
                    st.error('Could not find optimal pairs based on your selection. Please try again.')
                else:
                    optimal_pairs = res_optimal_pairs["data"]

                    des_id, type_des= get_location_id(destination.split(" (")[0])

                    res = get_final_cost(str(start_date), str(end_date), num_days, num_people, num_rooms, des_id, type_des, type_val, source_iata, destination_iata, budget)
                
                    if 'Airline' not in res["data"]:
                        st.error("Oops, looks like we couldn't find any flights for your combination! Please try again with different dates or destinations.")
                    else:                
                        startdate = res["data"]['start_date']
                        enddate = res["data"]['end_date']
                        hotel_name = res["data"]['hotel_name']
                        hotel_price = res["data"]['price']
                        flight_airline = res["data"]['Airline']
                        flight_price = res["data"]['Price']
                        total_cost = res["data"]['Total_cost']

                        print(res["data"])

                        if total_cost > budget:
                            st.warning(f"Uh oh! Looks like your budget is a bit tight for this trip. But don't worry, we've done our best to find the best options for you.")
                        
                        # User_name = 'Nishanth Prasath'
                        # user_email = 'nishanth@gmail.com'

                        currentRes = requests.post('http://localhost:8000/get_current_username',headers=headers)
                        currentUserEmail = currentRes.json()['username']
                        resUserName = requests.post('http://localhost:8000/get_current_name',json={'Username':currentUserEmail}).json()['Name']

                        User_name = resUserName
                        user_email = currentUserEmail

                        create_pdf_res = create_pdf(num_days, num_people, num_rooms, destination.split(" (")[0], type_val, source_iata, destination_iata, budget, startdate, enddate, hotel_name, hotel_price, startdate, enddate, flight_airline, flight_price, total_cost, User_name, optimal_pairs, selected_places, language, user_email)
                        
                        file_path = os.path.join('backend', user_email + "_itinerary.pdf")
                        file_name = user_email + '_itinerary.pdf'

                        if create_pdf_res["status_code"] == '200':
                            bucket_name = 'damg7245-team7'
                            key = 'Travelbud/'+file_name
                            common_utils.uploadfile(file_name, open(file_path, 'rb'))
                            url = common_utils.get_object_url(bucket_name, key)
                            print(url)
                            st.success('PDF Generated Successfully')
                            response = requests.get(url)
                            if response.status_code == 200:
                                with st.spinner('Downloading...'):
                                    st.download_button(
                                        label='Download File',
                                        data=response.content,
                                        file_name=User_name + ' Itinerary.pdf',
                                        mime='application/pdf'
                                    )
                            else:
                                st.error('Error downloading file. Please try again later.')
                        else:
                            st.error("Oops, looks like we couldn't find any travel plans matching your search criteria! Please try again with different dates or destinations.")

def my_account_page():
    # Set background image
    # st.markdown(f'<style>body{{background-image: url({page_bg}); background-size: cover;}}</style>', unsafe_allow_html=True)

    st.markdown("# TravelBud")
    st.subheader('My Account')
    # st.sidebar.markdown("# Page 3 🎉")
    st.sidebar.button("Logout")


    # Define the plans
    plans = {
        "Basic": "10",
        "Standard": "25",
        "Premium": "50"
    }

    # Create a radio button group to display the plans
    selected_plan = st.radio("Change your plan", list(plans.keys()))

    if selected_plan:
        # Display the selected plan's details
        st.info(f"You have selected the {selected_plan} plan. With the {selected_plan} plan, you can make {plans[selected_plan]} requests")
    
    
    # Display a multiselect for the user to choose the place types
    selected_place_types = st.multiselect('Update your interests', google_maps.get_place_types())

    # Display the user's selection
    if selected_place_types:
        st.info("You selected: " + ", ".join(selected_place_types))

    # Join the selected types with the '|' separator
    types_str = '|'.join(selected_place_types)

    st.button("Save")



def analytics_page():
    # Set background image
    # st.markdown(f'<style>body{{background-image: url({page_bg}); background-size: cover;}}</style>', unsafe_allow_html=True)
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    st.markdown("# TravelBud")
    st.subheader('Admin Dashboard - Welcome!')    
    # st.sidebar.markdown("# Page 3 🎉")
    
    try:
        fastapi_url="http://localhost:8000/get_useract_data"
        response=requests.get(fastapi_url,headers=headers)
        # print(response.json)
    except:
        print('user activity data not yet generated') 
        
    def convert_to_date(date_string,format):
    
        date_object = datetime.strptime(date_string.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
        
        if format=='date':
            return date_object.date().strftime('%Y-%m-%d')
        elif format=='hour':
            return date_object.hour
        elif format=='month':
            return date_object.month
        elif format=='week':
            return date_object.isocalendar()[1]

    # def user_act_data():
        
    #     last_date = datetime.strptime(user_activity['time_stamp'].iloc[-1].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
    #     time_diff = datetime.utcnow() - last_date
    #     if time_diff <= timedelta(days=30):
    #         api_hits=user_activity['hit_count'].iloc[-1]
    #         rem_limit=user_activity['api_limit'].iloc[-1]-api_hits
    #     else:
    #         api_hits=0
    #         rem_limit=user_activity['api_limit'].iloc[-1]
                
    #     return api_hits,rem_limit

    def data_charts(timeframe):
        
        if timeframe=='Day':
            # print(user_data.columns)
            
            daily_count = user_activity.groupby(['date_str'],as_index=False).agg({'Time_stamp': 'count'})
            daily_count = daily_count.reset_index()
            daily_count = daily_count.rename(columns={'Time_stamp': 'API Hits'})
            # print('y')
            return daily_count
        
        elif timeframe=='Week':
            week_count = user_activity.groupby(['week']).agg({'Time_stamp': 'count'})
            # reset index and rename columns
            week_count = week_count.reset_index()
            week_count = week_count.rename(columns={'Time_stamp': 'API Hits'})
            return week_count
        
        elif timeframe=='Month':
            month_count = user_activity.groupby(['month']).agg({'Time_stamp': 'count'})
            # reset index and rename columns
            month_count = month_count.reset_index()
            month_count = month_count.rename(columns={'Time_stamp': 'API Hits'})
            return month_count
        
    def make_chart(data,x_axis,y_axis,type,title):
        if type=='area':
            st.markdown(title)
            st.area_chart(
            data=data,
            x=x_axis,
            y=y_axis)
        elif type=='bar':
            st.markdown(title)
            st.bar_chart(
            data=data,
            x=x_axis,
            y=y_axis)
            
    def make_maps(data,timeframe):
        
        now = datetime.utcnow()
        
        if timeframe=='Day':
            # print(data['date_str'].iloc[0])
            df_map=data[data['date_str'] >= now.strftime('%Y-%m-%d')]
        elif timeframe == 'Week':
            df_map=data[data['week'] == now.isocalendar()[1]]
        elif timeframe == 'Month':
            df_map=data[data['month'] == now.month]

        st.map(df_map[['lat','lon']])

    def date_chart():
        grouped_data = user_activity.groupby(['S_Date']).nunique()['UserID']
        st.markdown('### Preffered Holiday Dates ')
        st.line_chart(grouped_data)

    try:
        if response.status_code==200:
            
            # print(response.json())
            plan_json=response.json()['plan']
            df_plan = pd.DataFrame(plan_json)
            aoi_json=response.json()['aoi']
            df_aoi = pd.DataFrame(aoi_json)
            
            user_data_json=response.json()['user_data']
            user_data = pd.DataFrame(user_data_json)
            
            user_act_json=response.json()['user_activity']
            # print(user_data_json['data'])
            user_activity = pd.DataFrame(user_act_json)
            user_activity['date_str']=user_activity['Time_stamp'].apply(convert_to_date,args=('date',))
            user_activity= user_activity.merge(user_data[['UserID','Plan']],on='UserID',how='left')
            user_activity= user_activity.merge(df_plan,left_on='Plan',right_on='plan_name',how='left')
            user_activity['hour']=user_activity['Time_stamp'].apply(convert_to_date,args=('hour',))
            user_activity['month']=user_activity['Time_stamp'].apply(convert_to_date,args=('month',)) 
            user_activity['week']=user_activity['Time_stamp'].apply(convert_to_date,args=('week',))
            airports=airportsdata.load('IATA')
            user_activity['lat']=user_activity['Source'].apply(lambda x: airports[x[-4:-1]]['lat'])
            user_activity['lon']=user_activity['Source'].apply(lambda x: airports[x[-4:-1]]['lon'])
            
            
        else:
            st.error("You haven't yet used our application")
            user_data=pd.DataFrame(columns=['UserID', 'Password', 'Name', 'Plan','Hit_count_left','Updated_time'])
            user_activity=pd.DataFrame(columns=['UserID', 'Source', 'Destination', 'S_Date', 'E_Date', 'Duration', 'Budget', 'TotalPeople', 'Time_stamp','date_str','api_limit','hour','month','week','lat','lon'])
            df_plan=pd.DataFrame(columns=['plan_name', 'api_limit'])
            df_aoi=pd.DataFrame(columns=['UserID', 'Interest'])
        
        # Row B
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Total Users", user_data['UserID'].nunique())
        b2.metric("Basic Users", user_data[user_data['Plan']=='Basic']['UserID'].nunique() )
        b3.metric("Standard Users", user_data[user_data['Plan']=='Standard']['UserID'].nunique())
        b4.metric("Premium Users", user_data[user_data['Plan']=='Premium']['UserID'].nunique())

        view_selection = st.radio("View by:",
                options=["Day", "Week", "Month"],
                horizontal=True
            )

        make_maps(user_activity,view_selection)
        
        if view_selection=="Day":
            data=data_charts('Day')
            recent_date=data['date_str'].iloc[-1]
            recent_data=data[data['date_str']==recent_date]
            all_data = data.groupby(['date_str'],as_index=False).agg({'API Hits': 'sum'})
            all_data = all_data.reset_index()
            # all_data = all_data.rename(columns={'date': 'API Hits'})
            make_chart(all_data,'date_str','API Hits','bar','### APP Usage - Daily')
        elif view_selection=="Week":
            data=data_charts('Week')
            recent_date=data['week'].iloc[-1]
            recent_data=data[data['week']==recent_date]
            make_chart(recent_data,'week','API Hits','bar','### APP Usage - Weekly ')
        elif view_selection=="Month":
            data=data_charts('Month')
            recent_date=data['month'].iloc[-1]
            recent_data=data[data['month']==recent_date]
            make_chart(recent_data,'month','API Hits','bar','### APP Usage - Monthly ')
            

        date_chart()
        st.markdown('### Budget Distribution')
        st.line_chart(user_activity['Budget'])

    except:
        print('empty table error')


pages = {
        "Home": home_page,
        "My Account": my_account_page,
        "Plan My Trip": plan_my_trip_page,
        "Analytics": analytics_page
    }
        
# Define the Streamlit app
def main():
    st.set_page_config(
        page_title="Travel Bud",page_icon=":earth_americas:" ,layout="wide"
    )
    st.sidebar.title("Navigation")

    # Check if user is signed in
    token = st.session_state.get("token", None)
    user_id = decode_token(token)

    # Render the navigation sidebar
    if user_id is not None and user_id != "admin":
        selection = st.sidebar.radio(
            "Go to", ["Home","My Account","Plan My Trip","Log Out"]
        )
    elif user_id == "admin":
        selection = st.sidebar.radio("Go to", ["Analytics", "Log Out"])
    else:
        selection = st.sidebar.radio("Go to", ["Sign In", "Sign Up", "Forget Password"])

    # Render the selected page or perform logout
    if selection == "Log Out":
        st.session_state.clear()
        st.sidebar.success("You have successfully logged out!")
        st.experimental_rerun()
    elif selection == "Sign In":
        token = login()
        if token is not None:
            st.session_state.token = token
            st.experimental_rerun()
    elif selection == "Sign Up":
        signup()
    elif selection == "Forget Password":
        forget_password()
    else:
        page = pages[selection]
        page()


if __name__ == "__main__":
    main()        