import os
import requests
from dotenv import load_dotenv
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm, SignInForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            first_name = form.cleaned_data['first_name']

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username is already taken.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered.")
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name
                )
                login(request, user)
                messages.success(request, f"Welcome, {user.first_name}!")
                return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user_obj = User.objects.filter(email=user_input).first() or User.objects.filter(username=user_input).first()
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
                if user:
                    login(request, user)
                    return redirect('index')
            messages.error(request, "Invalid username/email or password.")
    else:
        form = SignInForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def index_view(request):
    city = request.GET.get("city", "Puerto Princesa")
    load_dotenv(override=True)
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    weather_data = {}
    
    if not api_key or api_key == "your_openweather_api_key_here":
        weather_data = {
            "error": "OpenWeather API Key is missing. Please check OPENWEATHER_API_KEY in your .env file."
        }
    else:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            weather_data = {
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temp": data.get("main", {}).get("temp"),
                "feels_like": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "description": data.get("weather", [{}])[0].get("description", "").title(),
                "icon": data.get("weather", [{}])[0].get("icon"),
            }
        except requests.exceptions.RequestException as e:
            weather_data = {"error": "Failed to fetch weather data.", "details": str(e)}
        except KeyError:
            weather_data = {"error": f"Could not find weather information for '{city}'."}

    return render(request, 'index.html', {
        'weather': weather_data,
        'city': city
    })

@login_required
def gemini_chat_api(request):
    if request.method == 'POST':
        load_dotenv(override=True)
        prompt = request.POST.get('prompt', '').strip()
        if not prompt:
            return JsonResponse({'error': 'Prompt cannot be empty.'}, status=400)

        gemini_key = os.getenv("GEMINI_API_KEY", "").strip().strip("'\"")
        if not gemini_key or gemini_key == "your_gemini_api_key_here":
            return JsonResponse({'error': 'GEMINI_API_KEY missing in .env file.'}, status=500)

        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"

        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                res_data = res.json()
                reply = res_data['candidates'][0]['content']['parts'][0]['text']
                return JsonResponse({'reply': reply})

            err_msg = res.json().get('error', {}).get('message', res.text)
            return JsonResponse({'error': f'Gemini API Access Error: {err_msg}'}, status=500)

        except Exception as e:
            return JsonResponse({'error': f'Connection error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def serviceworker_view(request):
    sw_code = """
const CACHE_NAME = 'cozy-ai-pwa-v1';
const urlsToCache = [
  '/',
  '/login/',
  '/register/',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
"""
    return HttpResponse(sw_code, content_type='application/javascript')