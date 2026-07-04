from fpdf import FPDF
import openai
import os
from dotenv import load_dotenv

load_dotenv()


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
        temperature=0.15
    )

    # Grab just the text from the API completion response
    reply_content = completion.choices[0].message.content

    # Append the generated response to the message history
    message_history.append({"role": "assistant", "content": f"{reply_content}"})

    # Return the generated response.
    return reply_content


def create_pdf(User_name, start_date, end_date, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, hotel_name, price, airline, flight_price, total_cost, locations, pairing):
    prompt = create_itinerary(User_name, start_date, end_date, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, hotel_name, price, airline, flight_price, total_cost, locations, pairing)
    message_history = []
    gpt_response = chat(prompt, message_history)


    pdf = MyPDF()
    pdf.add_page()
    text = gpt_response
    pdf.create_page(text)
    pdf.output(User_name + " itinerary.pdf")

# from the streamlit user input
num_days_val = 3
adults_number_val = 1
num_rooms_val = '1'
detination_name_val = 'New York'
type_val = 'Best'
origin_val = 'BOS'
destination_val = 'JFK'
budget_val = 1000

# from the booking.py file fn:get_final_cost
start_date = '2023-10-02'
end_date = '2023-10-04'
hotel_name = 'West 119th B&B' 
price = 378.675
flight_start_date = '2023-10-02'
flight_end_date = '2023-10-04'
airline = 'American Airlines'
flight_price = 158.0
total_cost = 536.675


User_name = 'Dhanush Kumar' #based on login

# from the google maps.py file
pairing = """Optimal pairs:
Edge NY and Empire State NY: 1.726 km
Brookline Bridge NY and Statue of Liberty NY: 3.771 km
Left out location: Central Park NY"""

#from the streamlit user input
locations = ['Edge NY', 'Empire State NY', 'Brookline Bridge NY', 'Central Park NY', 'Statue of Liberty NY']
create_pdf(User_name, start_date, end_date, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, hotel_name, price, airline, flight_price, total_cost, locations, pairing)