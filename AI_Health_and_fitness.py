import os
import time
import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.exceptions import ModelProviderError

# Set API Key 
GOOGLE_API_KEY = "Put your key here"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

#Helper function to handle rate limits
def safe_run(agent, prompt, retries=3, delay=2):
    """Run agent with retry logic on rate-limit errors (HTTP 429)."""
    for i in range(retries):
        try:
            return agent.run(prompt)
        except ModelProviderError as e:
            if "429" in str(e):
                st.warning(f"Rate limit hit. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                raise
    raise Exception("Failed after multiple retries due to rate limiting.")

#Dietary Planner Agent 
dietary_planner = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    description="Creates personalized dietary plans based on user input.",
    instructions=[
        "Generate a diet plan with breakfast, lunch, dinner, and snacks.",
        "Consider dietary preferences like Keto, Vegetarian, or Low Carb.",
        "Ensure proper hydration and electrolyte balance.",
        "Provide nutritional breakdown including macronutrients and vitamins.",
        "Suggest meal preparation tips for easy implementation.",
        "If necessary, search the web using DuckDuckGo for additional information.",
    ],
    tools=[DuckDuckGoTools()],
    markdown=True
)

# Fitness Trainer Agent 
fitness_trainer = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    description="Generates customized workout routines based on fitness goals.",
    instructions=[
        "Create a workout plan including warm-ups, main exercises, and cool-downs.",
        "Adjust workouts based on fitness level: Beginner, Intermediate, Advanced.",
        "Consider weight loss, muscle gain, endurance, or flexibility goals.",
        "Provide safety tips and injury prevention advice.",
        "Suggest progress tracking methods for motivation.",
        "If necessary, search the web using DuckDuckGo for additional information.",
    ],
    tools=[DuckDuckGoTools()],
    markdown=True
)

#Team Lead Agent 
team_lead = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    description="Combines diet and workout plans into a holistic health strategy.",
    instructions=[
        "Merge personalized diet and fitness plans for a comprehensive approach, Use Tables if possible.",
        "Ensure alignment between diet and exercise for optimal results.",
        "Suggest lifestyle tips for motivation and consistency.",
        "Provide guidance on tracking progress and adjusting plans over time."
    ],
    markdown=True
)

#Functions to get plans
def get_meal_plan(age, weight, height, activity_level, dietary_preference, fitness_goal):
    prompt = (f"Create a personalized meal plan for a {age}-year-old person, weighing {weight}kg, "
              f"{height}cm tall, with an activity level of '{activity_level}', following a "
              f"'{dietary_preference}' diet, aiming to achieve '{fitness_goal}'.")
    return safe_run(dietary_planner, prompt)

def get_fitness_plan(age, weight, height, activity_level, fitness_goal):
    prompt = (f"Generate a workout plan for a {age}-year-old person, weighing {weight}kg, "
              f"{height}cm tall, with an activity level of '{activity_level}', "
              f"aiming to achieve '{fitness_goal}'. Include warm-ups, exercises, and cool-downs.")
    return safe_run(fitness_trainer, prompt)

def get_full_health_plan(name, age, weight, height, activity_level, dietary_preference, fitness_goal):
    meal_plan = get_meal_plan(age, weight, height, activity_level, dietary_preference, fitness_goal)
    fitness_plan = get_fitness_plan(age, weight, height, activity_level, fitness_goal)

    return safe_run(
        team_lead,
        f"Greet the customer, {name}\n\n"
        f"User Information: {age} years old, {weight}kg, {height}cm, activity level: {activity_level}.\n\n"
        f"Fitness Goal: {fitness_goal}\n\n"
        f"Meal Plan:\n{meal_plan}\n\n"
        f"Workout Plan:\n{fitness_plan}\n\n"
        f"Provide a holistic health strategy integrating both plans."
    )

#Streamlit UI 
st.set_page_config(page_title="AI Health & Fitness Plan", page_icon="🏋️‍♂️", layout="wide")

# Custom Styles
st.markdown("""
    <style>
        .title { text-align: center; font-size: 48px; font-weight: bold; color: #FF6347; }
        .subtitle { text-align: center; font-size: 24px; color: #4CAF50; }
        .goal-card { padding: 20px; margin: 10px; background-color: #FFF; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);color: #333333; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">🏋️‍♂️ AI Health & Fitness Plan Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Personalized fitness and nutrition plans to help you achieve your health goals!</p>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Health & Fitness Inputs")

# User Inputs
name = st.text_input("What's your name?", "FJ")
age = st.sidebar.number_input("Age (in years)", min_value=10, max_value=100, value=25)
weight = st.sidebar.number_input("Weight (in kg)", min_value=30, max_value=200, value=70)
height = st.sidebar.number_input("Height (in cm)", min_value=100, max_value=250, value=170)
activity_level = st.sidebar.selectbox("Activity Level", ["Low", "Moderate", "High"])
dietary_preference = st.sidebar.selectbox("Dietary Preference", ["Keto", "Vegetarian", "Low Carb", "Balanced"])
fitness_goal = st.sidebar.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "Endurance", "Flexibility"])

st.markdown("---")

# Generate Plan
if st.sidebar.button("Generate Health Plan"):
    if not age or not weight or not height:
        st.sidebar.warning("Please fill in all required fields.")
    else:
        with st.spinner("💥 Generating your personalized health & fitness plan..."):
            try:
                full_health_plan = get_full_health_plan(name, age, weight, height, activity_level, dietary_preference, fitness_goal)
                st.subheader("Your Personalized Health & Fitness Plan")
                st.markdown(full_health_plan.content if hasattr(full_health_plan, "content") else full_health_plan)
                st.info("This is your customized health and fitness strategy, including meal and workout plans.")

                # Motivational Message
                st.markdown("""
                    <div class="goal-card">
                        <h4>🏆 Stay Focused, Stay Fit!</h4>
                        <p>Consistency is key! Keep pushing yourself, and you will see results. Your fitness journey starts now!</p>
                        <p>❤️FJ</p>                        
                    </div> 
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"⚠️ Error generating plan: {str(e)}")
