import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AVIATIONSTACK_API_KEY")

def search_flights(origin_code, destination_code):
    url = "http://api.aviationstack.com/v1/flights"

    params = {
    "access_key": api_key,
    "dep_iata": origin_code,
    "arr_iata": destination_code,
    "limit": 5
    }

    response = requests.get(url, params=params)
    data = response.json()
    flights = []

    if "data" in data and len(data["data"]) > 0:

        for flight in data["data"][:5]:

            flights.append(
                f"""
                Airline: {flight['airline']['name']}
                Flight Number: {flight['flight']['number']}
                Departure: {flight['departure']['airport']}
                Arrival: {flight['arrival']['airport']}
                Status: {flight['flight_status']}
                """
                )

        return "\n".join(flights)

    return "No flights found"