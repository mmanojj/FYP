from flask import Flask, request, jsonify
from helper.database_api import save_user_data, get_user_data, save_appointment, get_all_appointment_texts,save_personal_information,save_medical_information,get_personal_information,get_medical_information,clear_all_data
from datetime import datetime
import os
import openai
import requests
import random
import urllib.parse

#initialisations
openai_api_key = os.getenv("OPENAI_API_KEY")
spoonacular_api_key = os.getenv("SPOONACULAR_API_KEY")
spoonacular_base_url = "https://api.spoonacular.com/recipes"

app = Flask(__name__)

@app.route('/')
def home():
    return 'OK', 200

@app.route('/dialogflow', methods=['POST'])
def dialogflow():
    data = request.get_json()
    intent_name = data['queryResult']['intent']['displayName']
    
    if intent_name == 'SaveUserName':
        # Extract the name from the request
        name = data['queryResult']['parameters'].get('person', [{}])[0].get('name', None)
        if name:
            # Save the name to the database
            save_user_data('name', name)
            response_text = f"Your name, {name}, has been saved. What else can I help you with?"
        else:
            response_text = "Sorry, I didn't catch your name. Can you please provide it again?"
    
    elif intent_name == 'RetrieveUserName':
        user_name = get_user_data('name')
        if user_name:
            response_text = f"Here is your name: {user_name}"
        else:
            response_text = "Sorry, I couldn't find any information for your name."

    elif intent_name == 'Entertainment':
        user_query = data['queryResult']['queryText']
        response = generate_chatgpt_response(user_query)
        return jsonify({
            "fulfillmentMessages": [{
                "text": {"text": [response]}
            }]
        }), 200

    elif intent_name == 'Default Fallback':
        # Extract user query
        user_query = data['queryResult']['queryText']
        
        # Call ChatGPT to generate response
        response = generate_chatgpt_response(user_query)
        
        # Return ChatGPT response
        return jsonify({
            "fulfillmentMessages": [{
                "text": {"text": [response]}
            }]
        }), 200

    elif intent_name == 'Appointment Scheduler':
        activity = data['queryResult']['parameters'].get('activity', None)
        time = data['queryResult']['parameters'].get('time', None)
        date = data['queryResult']['parameters'].get('date', None)

        if activity and time and date:
            human_readable_time = convert_time_to_human_readable(time)
            human_readable_date = convert_date_to_human_readable(date)
            save_appointment(activity, human_readable_time, human_readable_date)
            response_text = f"Your {activity} appointment is set at {human_readable_time} on {human_readable_date}."
        else:
            response_text = "Sorry, I couldn't schedule the appointment. Please provide all details."

    elif intent_name == 'RetrieveAppointment':
        appointment_texts = get_all_appointment_texts()
        if appointment_texts:
            response_text = "Here are your appointment details:\n"
            for appointment_text in appointment_texts:
                response_text += f"- {appointment_text}\n"
        else:
            response_text = "You don't have any appointments scheduled."

    elif intent_name == 'End Conversation':
        user_name = get_user_data('name')
        if user_name:
            response_text = f"Goodbye, {user_name}! It was nice talking to you."
        else:
            response_text = "Goodbye! Have a great day."
        clear_all_data()

    elif intent_name == 'Exercise Recommendations':
    # Respond with exercise recommendations
        response_text = "Certainly! Exercise is important for maintaining good health and well-being. Physical inactivity can contribute to developing issues such as chronic pain and osteoporosis. Do remember to exercise caution and consult a healthcare professional before starting on the exercise routines. What type of exercise would you like to check out? (Low, Medium, High intensity)"

    elif intent_name == 'ExerciseRecommendations - low':
        response_text = "Starting out with simple exercises is a great idea. Here are a few low intensity exercises for you to consider: \n\n1.Walking\n2.Tai Chi\n3.Chair Yoga \n\nChoose one to find out more about the exercise."

    elif intent_name == 'ExerciseRecommendations - medium':
        response_text = "Medium intensity workouts are helpful in retaining/growing muscles while not over exerting yourself. Here are a few medium intensity exercises for you to consider: \n\n1.Water Aerobics\n2.Stationary Cycling\n3.Dancing \n\nChoose one to find out more about the exercise."

    elif intent_name == 'ExerciseRecommendations - high':
        response_text = "High intensity workouts are very beneficial but must be done cautiously. Here are a few high intensity exercises for you to consider: \n\n1.Interval Training\n2.Stength Training with resistance bands\n3.Swimming \n\nChoose one to find out more about the exercise."

    elif intent_name == 'Recipe Recommendations':
        cuisine = data['queryResult']['parameters'].get('cuisine', None)
        diet = data['queryResult']['parameters'].get('diet', None)
        recipe = get_recipe(cuisine, diet)
        response_text = recipe

    elif intent_name == 'Trivia Game':
        # Make a request to Open Trivia Database API
        url = "https://opentdb.com/api.php?amount=40&type=multiple&encode=url3986&category=9"
        response = requests.get(url)
  
        if response.status_code == 200:
            trivia_data = response.json()
            # Select a random trivia question and answer
            index = random.randint(0, len(trivia_data['results']) - 1)
            question = urllib.parse.unquote(trivia_data['results'][index]['question'])
            answer = urllib.parse.unquote(trivia_data['results'][index]['correct_answer'])
            secret_answer = f'{answer}'  
            return jsonify({
                "fulfillmentMessages": [{
                    "text": {"text": [f"Question: {question}\n\n\n\n\n\n\n\n\n\nAnswer: {secret_answer}"]}
                }]
            }), 200
        else:
            return jsonify({
                "fulfillmentMessages": [{
                    "text": {"text": ["Sorry, I couldn't fetch a trivia question at the moment."]}
                }]
            }), 200

    elif intent_name == 'SavePersonalInformation':
        personal_info = data['queryResult']['queryText'].split(': ', 1)[1]
        save_personal_information(personal_info)
        response_text = "Your personal information has been saved successfully."

    elif intent_name == 'RetrievePersonalInformation':
        personal_info = get_personal_information()
        user_name = get_user_data('name')
        if user_name:
            response_text = f"Here is your personal information, {user_name}: {', '.join(personal_info)}"
        else:
            response_text = f"Here is your personal information: {', '.join(personal_info)}"

    elif intent_name == 'SaveMedicalInformation':
        medical_info = data['queryResult']['queryText'].split(': ', 1)[1]
        save_medical_information(medical_info)
        response_text = "Your medical information has been saved successfully."

    elif intent_name == 'RetrieveMedicalInformation':
        medical_info = get_medical_information()
        user_name = get_user_data('name')
        if user_name:
            response_text = f"Here is your medical information, {user_name}: {', '.join(medical_info)}"
        else:
            response_text = f"Here is your medical information: {', '.join(medical_info)}"

    elif intent_name == 'Scope Explanation':
        response_text = "Here is a list of tasks I can help you with\n\n1. Emergency Assistance (Ask smth like 'How do I get help in an emergency?') \n2. Entertainment (Ask for movie/song recommendations or even jokes)\n3. Nutrition Advice (Ask smth like 'Recommend me a balanced diet') \n4. Health Issues (Ask smth like 'What diseases am I prone to?')\n5. Health Tips (Ask smth like 'How to stay healthy')\n6. Mental Fitness (Ask smth like 'How to stay mentally fit')\n7. Excercise Recommendations (Ask smth like 'Recommend me a workout routine')\n8. Recipe Recommendations (Ask smth like 'Suggest me a recipe with low-fat diet and mexican cusine')\n9. Trivia (Ask smth like 'suggest trivia questions')\n10. Appt Scheduling (Say smth like 'Set an appointment for 2pm Tuesday at the dentist')\n11. Saving Medical Info (Say smth like 'This is my medical information:...')\n12. Saving Personal Info (Say smth like 'This is my personal information:...')\n13. Retrival (Say smth like 'retrieve my appointments' or 'retrieve my medical info')"
    
    else:
        response_text = "Sorry, I'm not sure how to handle that intent."
    
    return jsonify({
        "fulfillmentMessages": [{
            "text": {"text": [response_text]}
        }]
    }), 200

def generate_chatgpt_response(user_query):
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",  
        prompt=user_query,
        max_tokens=150  
    )
    return response.choices[0].text.strip()

def get_recipe(cuisine, diet):
    # Construct the URL for fetching recipes
    url = f"{spoonacular_base_url}/complexSearch?apiKey={spoonacular_api_key}&cuisine={cuisine}&diet={diet}&number=2"

    # Make an HTTP GET request to fetch recipes
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the JSON response
        recipe_data = response.json()
        # Select a random recipe from the list
        random_recipe = random.choice(recipe_data['results'])
        # Extract the title of the selected recipe
        recipe_title = random_recipe['title']
        # Get the instructions for the selected recipe
        recipe_id = random_recipe['id']
        instruction_url = f"{spoonacular_base_url}/{recipe_id}/information?apiKey={spoonacular_api_key}"
        instruction_response = requests.get(instruction_url)
        if instruction_response.status_code == 200:
            instruction_data = instruction_response.json()
            recipe_instructions = instruction_data['instructions']
            return f"Random Recipe: {recipe_title}\nInstructions: {recipe_instructions}"
        else:
            return "Failed to fetch recipe instructions"
    else:
        return "Failed to fetch recipes"

def convert_date_to_human_readable(date_str):
  date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
  human_readable_date = date_obj.strftime("%A, %B %d, %Y")  
  return human_readable_date


def convert_time_to_human_readable(time_str):
  datetime_obj = datetime.fromisoformat(time_str)
  time_obj = datetime_obj.time()
  human_readable_time = time_obj.strftime("%I:%M %p")
  return human_readable_time
