import os
import json
import random
from typing import TypedDict, Annotated
import operator
import psycopg
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, AnyMessage
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()
from tools.tavily_tool import search_hotels
from tools.flight_tool import search_flights

llm = ChatGroq(model="llama-3.3-70b-versatile")

DATABASE_URL = os.getenv('DATABASE_URL')

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

def travel_parser_agent(state: TravelState):

    prompt = f"""
    Extract travel details from the query and convert travel locations into IATA airport codes.
    Rules:
    -Use the most popular international airport
    -If a Country is mentioned instead of a city, use the capital city's airport code.

    Return ONLY JSON.

    Example:
    {{
        "origin_code":"DEL",
        "destination_code":"JFK",
        "budget":"300000",
        "days":"7"
    }}

    Query:
    {state['user_query']}
    """

    response = llm.invoke([
        SystemMessage(content="Travel extraction assistant"),
        HumanMessage(content=prompt)
    ])
    response_text = response.content.strip()

    response_text = response_text.replace("```json", "")
    response_text = response_text.replace("```", "")
    response_text = response_text.strip()
    return {
        "user_query": response_text,
        "messages": [AIMessage(content="Travel details extracted")],
        "llm_calls": state.get("llm_calls",0)+1
    }


def flight_agent(state:TravelState):
    query_data = json.loads(state['user_query'])
    origin_code = query_data.get("origin_code")
    destination_code = query_data.get("destination_code")
    flight_data = search_flights(origin_code, destination_code)
    return {
        'flight_results': flight_data,
        'messages': [AIMessage(content=f"Flight results fetched")],
        'llm_calls': state.get('llm_calls', 0) + 1
    }


def hotel_agent(state:TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = search_hotels(query)
    return {
        'hotel_results': hotel_results,
        'messages': [AIMessage(content=f"Hotel results fetched")],
        'llm_calls': state.get('llm_calls', 0) + 1
    }


def research_agent(state:TravelState):
    prompt = f"""
    User Query: {state['user_query']}
    
    Flight Results:
    {state['flight_results']}
    
    Hotel Results:
    {state['hotel_results']}
    
    Extract and organize the travel information.

    Return ONLY:

    1. Flight Information
    2. Hotel Recommendations
    3. Places to Visit
    4. Estimated Budget

    Do NOT create a day-wise itinerary.
    Do NOT write a final travel plan.
    Keep it concise.
    """
    response = llm.invoke([SystemMessage(content="You are a helpful travel assistant."), HumanMessage(content=prompt)])
    return {
        'itinerary': response.content,
        'messages': [response],
        'llm_calls': state.get('llm_calls', 0) + 1
    }


def final_agent(state:TravelState):
    prompt = f"""
        Create a professional travel plan using:

        Flight Information:
        {state['flight_results']}

        Hotel Information:
        {state['hotel_results']}

        Travel Research:
        {state['itinerary']}

        User Request:
        {state['user_query']}

        Requirements:
        - Create a detailed day-wise Final Traavel Plan
        - Include hotel recommendation
        - Include budget breakdown
        - Include travel tips
        - Make the response user-friendly
        - Use headings and bullet points
    """
    response = llm.invoke([SystemMessage(content="You are a helpful travel assistant."), HumanMessage(content=prompt)])
    return {
        'messages': [response],
        'llm_calls': state.get('llm_calls', 0) + 1
    }


graph = StateGraph(TravelState)
graph.add_node('travel_parser_agent', travel_parser_agent)
graph.add_node('flight_agent', flight_agent)
graph.add_node('hotel_agent', hotel_agent)
graph.add_node('research_agent', research_agent)
graph.add_node('final_agent', final_agent)

graph.add_edge(START, 'travel_parser_agent')
graph.add_edge('travel_parser_agent', 'flight_agent')
graph.add_edge('flight_agent', 'hotel_agent')
graph.add_edge('hotel_agent', 'research_agent')
graph.add_edge('research_agent', 'final_agent')
graph.add_edge('final_agent', END)

# Initialize Postgres checkpoint server
_connection = psycopg.connect(DATABASE_URL,autocommit=True)
checkpointer = PostgresSaver(_connection)
checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    thread_id = f"user_vansh{random.randint(100,999)}"
    config = {
        'configurable': {
            'thread_id': thread_id,
        }
    }

    user_input = input("Enter your travel request: ")

    result = app.invoke({
        'messages': [HumanMessage(content=user_input)],
        'user_query': user_input,
        'flight_results': '',
        'hotel_results': '',
        'itinerary': '',
        'llm_calls': 0
    },
    config=config
    )

    for message in result['messages']:
        print(message.content)

