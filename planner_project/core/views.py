# core/views.py
import os
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
import google.generativeai as genai


api1= os.getenv("GOOGLE_API_KEY")
# Configure the Gemini API
genai.configure(api_key=api1)

# --- Authentication Views ---
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'core/login.html', {'form': form, 'page': 'signup'})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form, 'page': 'login'})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- Main Application View with AI ---
@login_required
def index(request):
    if request.method == 'POST':
        destination = request.POST.get('destination')
        days = request.POST.get('days')
        interests = request.POST.get('interests')

        # Use the Gemini 1.5 Pro model
        model = genai.GenerativeModel('gemini-1.5-pro-latest') # <-- 👈 UPDATED

        # AI Module 1: Itinerary Generation
        itinerary_prompt = f"""
        Create a detailed travel itinerary for a trip to {destination} for {days} days.
        The user is interested in: {interests}.
        Provide the output as a JSON object with a key 'itinerary' which is an array of objects,
        where each object represents a day and has 'day', 'title', and 'activities' (a string with a detailed plan for the day).
        Example format: {{"itinerary": [{{"day": 1, "title": "Arrival and Exploration", "activities": "..."}}]}}
        """
        response = model.generate_content(itinerary_prompt)
        
        try:
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            itinerary_data = json.loads(cleaned_response)
        except (json.JSONDecodeError, AttributeError):
            itinerary_data = {"error": "Could not generate itinerary. Please try again."}


        # AI Module 2: Local Recommendations
        recommendations_prompt = f"""
        Based on the interests '{interests}', suggest 3 unique local restaurants and 3 offbeat activities in {destination} that are not typical tourist traps.
        Provide the output as a JSON object with two keys: 'restaurants' and 'activities', each an array of objects with 'name' and 'description'.
        Example format: {{"restaurants": [{{"name": "Local Gem", "description": "..."}}], "activities": [{{"name": "Hidden Trail", "description": "..."}}]}}
        """
        reco_response = model.generate_content(recommendations_prompt)
        
        try:
            cleaned_reco = reco_response.text.strip().replace("```json", "").replace("```", "")
            recommendation_data = json.loads(cleaned_reco)
        except (json.JSONDecodeError, AttributeError):
            recommendation_data = {"error": "Could not fetch recommendations."}
        
        context = {
            'itinerary': itinerary_data.get('itinerary'),
            'recommendations': recommendation_data,
            'destination': destination
        }
        return render(request, 'core/index.html', context)
        
    return render(request, 'core/index.html')