import googlemaps
from itertools import combinations
import os
from dotenv import load_dotenv


load_dotenv()



def find_optimal_pairs(locations):

    gmaps = googlemaps.Client(key= os.environ.get('GOOGLE_MAPS_API_KEY'))

    location_pairs = list(combinations(locations, 2))

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

    left_out_locations = set(locations) - visited_locations

    result_str = ""
    day = 1
    for pair, distance in optimal_pairs:
        result_str += f"Day {day}: {pair[0]} and {pair[1]}: {distance} km\n"
        day += 1

    if left_out_locations:
        result_str += f"Day {day}: Left out location: {' '.join(left_out_locations)}"

    return result_str



locations = ['Wild Florida Airboats & Gator Park Florida', 'Edison & Ford Winter Estates Florida', 'The John and Mable Ringling Museum of Art Florida', 'The Dalí (Salvador Dalí Museum) Florida', "Universal's Islands of Adventure Florida"]
# output = find_optimal_pairs(locations)
# print(output)




def get_place_types():
    
    # list of place type names based on the Google Places API documentation
    return [
        "accounting",
        "airport",
        "amusement_park",
        "aquarium",
        "art_gallery",
        "atm",
        "bakery",
        "bank",
        "bar",
        "beauty_salon",
        "bicycle_store",
        "book_store",
        "bowling_alley",
        "bus_station",
        "cafe",
        "campground",
        "car_dealer",
        "car_rental",
        "car_repair",
        "car_wash",
        "casino",
        "cemetery",
        "church",
        "city_hall",
        "clothing_store",
        "convenience_store",
        "courthouse",
        "dentist",
        "department_store",
        "doctor",
        "drugstore",
        "electrician",
        "electronics_store",
        "embassy",
        "fire_station",
        "florist",
        "funeral_home",
        "furniture_store",
        "gas_station",
        "gym",
        "hair_care",
        "hardware_store",
        "hindu_temple",
        "home_goods_store",
        "hospital",
        "insurance_agency",
        "jewelry_store",
        "laundry",
        "lawyer",
        "library",
        "light_rail_station",
        "liquor_store",
        "local_government_office",
        "locksmith",
        "lodging",
        "meal_delivery",
        "meal_takeaway",
        "mosque",
        "movie_rental",
        "movie_theater",
        "moving_company",
        "museum",
        "night_club",
        "painter",
        "park",
        "parking",
        "pet_store",
        "pharmacy",
        "physiotherapist",
        "plumber",
        "police",
        "post_office",
        "primary_school",
        "real_estate_agency",
        "restaurant",
        "roofing_contractor",
        "rv_park",
        "school",
        "secondary_school",
        "shoe_store",
        "shopping_mall",
        "spa",
        "stadium",
        "storage",
        "store",
        "subway_station",
        "supermarket",
        "synagogue",
        "taxi_stand",
        "tourist_attraction",
        "train_station",
        "transit_station",
        "travel_agency",
        "university",
        "veterinary_care",
        "zoo"
    ]