from fpdf import FPDF
import openai
import os
from dotenv import load_dotenv
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

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


def create_pdf(User_name, start_date, end_date, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, hotel_name, price, airline, flight_price, total_cost, locations, pairing, language):
    prompt = create_itinerary(User_name, start_date, end_date, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, hotel_name, price, airline, flight_price, total_cost, locations, pairing)
    message_history = []
    gpt_response = chat(prompt, message_history)

    if language == "Spanish":
        gpt_response = translate_text(gpt_response, 'Spanish')

    if language == "Hindi":
        gpt_response = translate_text(gpt_response, 'Hindi')
    
    pdf = MyPDF()
    pdf.add_page()
    text = gpt_response
    pdf.create_page(text)
    pdf.output(User_name + " itinerary.pdf")

# from the streamlit user input
num_days_val = 3
adults_number_val = 1
num_rooms_val = '1'
detination_name_val = 'Florida'
type_val = 'Best'
origin_val = 'BOS'
destination_val = 'MCO'
budget_val = 1000

# from the booking.py file fn:get_final_cost
start_date = '2023-09-28'
end_date = '2023-09-30'
hotel_name = 'Hoosville Hostel (Formerly The Everglades Hostel)' 
price = 73.224
flight_start_date = '2023-09-28'
flight_end_date = '2023-09-30'
airline = 'Frontier Airlines'
flight_price = 130
total_cost = 203.224


User_name = 'Dhanush Kumar' #based on login

# from the google maps.py file
pairing = """
The John and Mable Ringling Museum of Art Florida and The Dalí (Salvador Dalí Museum) Florida: 54.403 km
Wild Florida Airboats & Gator Park Florida and Universal's Islands of Adventure Florida: 58.509 km
Edison & Ford Winter Estates Florida"""

# from the streamlit user input
locations = ['Wild Florida Airboats & Gator Park Florida', 'Edison & Ford Winter Estates Florida', 'The John and Mable Ringling Museum of Art Florida', 'The Dalí (Salvador Dalí Museum) Florida', "Universal's Islands of Adventure Florida"]
create_pdf(User_name, start_date, end_date, num_days_val, adults_number_val, num_rooms_val, detination_name_val, type_val, origin_val, destination_val, budget_val, hotel_name, price, airline, flight_price, total_cost, locations, pairing, "French")