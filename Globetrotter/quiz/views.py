import json
import random
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache  # Redis cache
from quiz.models import User  # PostgreSQL User model
from pymongo import MongoClient
import redis
import os
from django.db import transaction
from django.shortcuts import reverse
import urllib.parse
import requests  # To make an internal API call to register the inviter


MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_DB_USERNAME = os.getenv("MONGO_DB_ROOT_USERNAME")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_ROOT_PASSWORD")
COLLECTION_NAME = "destinations"

# Initialize Redis and MongoDB
redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
mongo_client = MongoClient(
    "mongodb://mongo_user:mongo_pass@mongodb:27017/",
    authSource="admin"  # 👈 Ensure authentication happens in the "admin" database
)
mongo_db = mongo_client.get_database("globetrotter_mongo")
destination_collection = mongo_db[COLLECTION_NAME]


# 🔹 Generate JWT Token
def create_token(username):
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        'username': username,
        'exp': expiration
    }
    secret_key = settings.SECRET_KEY  # Get secret key from .env
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

# 🔹 Verify JWT Token
def check_token(token):
    if not token:
        return False
    try:
        secret_key = settings.SECRET_KEY
        decoded_payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        username = decoded_payload.get('username')

        if not username:
            return False

        # 🔹 Check in Redis first
        user_data = cache.get(f"user:{username}")
        if user_data:
            return decoded_payload.get('username') # Return user data from Redis

        # 🔹 If not found in Redis, check PostgreSQL
        user = User.objects.get(username=username)

        # 🔹 Cache user in Redis (Expire in 1 hour)
        cache.set(f"user:{username}", json.dumps({
            "username": user.username,
            "correct_answers": user.correct_answers,
            "incorrect_answers": user.incorrect_answers
        }), timeout=3600)

        return decoded_payload.get('username')

    except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
        return False


# 🔹 User Signup
@api_view(["POST"])
def register(request):
    username = request.data.get("username")
    if not username:
        return Response({"error": "Username is required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already registered"}, status=400)

    user = User(username=username, correct_answers=0, incorrect_answers=0)
    user.save()

    # Store user in Redis
    redis_client.hset(f"user:{username}", mapping={
        "correct_answers": 0,
        "incorrect_answers": 0
    })
    return Response({"Token": create_token(username)})

# 🔹 User Login
@api_view(["POST"])
def login(request):
    username = request.data.get("username")
    if not username:
        return Response({"error": "Username is required"}, status=400)

    user_key = f"user:{username}"

    # ✅ Check if user exists in Redis
    if redis_client.exists(user_key):
        return Response({"Token": create_token(username)})

    # ✅ If not in Redis, check PostgreSQL
    user = User.objects.filter(username=username).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    # ✅ Store user in Redis
    redis_client.hset(user_key, mapping={
        "correct_answers": user.correct_answers,
        "incorrect_answers": user.incorrect_answers
    })

    return Response({"Token": create_token(username)})

# 🔹 Fetch Next Question
@api_view(["GET"])
def next_question(request):
    authfromheader = request.headers.get("Authorization")

    if not authfromheader:
        authfromheader = request.query_params.get("token") 

    # print(request.query_params.get("token"))


    user = check_token(authfromheader)

    
    if not user:
        return Response({"error": "Unauthorized"}, status=401)

    pointer = int(redis_client.get('global_pointer') or 0)  # Default to 0

    # ✅ Fetch destination as JSON string from Redis list
    destination_json = redis_client.lindex("destinations", pointer)

    if not destination_json:
        return Response({"error": "No destinations available"}, status=404)

    destination = json.loads(destination_json)  # Convert back to dictionary

    # ✅ Get all destination names & pick random options
    all_names = redis_client.lrange("destination_names", 0, -1)  # Get all names
    correct_answer = f"{destination['city']}, {destination['country']}"
    options = random.sample([name for name in all_names if name != correct_answer], 3) + [correct_answer]
    random.shuffle(options)

    # ✅ Update pointer for next question (round-robin)
    redis_client.set('global_pointer', (pointer + 1) % redis_client.llen('destinations'))

    return Response({
        "clues": destination["clues"],
        "options": options,
        "pointer": pointer
    })

# 🔹 Validate Answer & Update Score
@api_view(["POST"])
def submit_answer(request):
    authfromheader = request.headers.get("Authorization")
    if not authfromheader:
        authfromheader = request.data.get("token") 
    username = check_token(authfromheader)
    if not username:
        return Response({"error": "Unauthorized"}, status=401)

    pointer = int(request.data.get("pointer", -1))
    selected_answer = request.data.get("answer")

    if pointer == -1 or not selected_answer:
        return Response({"error": "Invalid request"}, status=400)

    # Get the correct answer
    destination_json = redis_client.lindex("destinations", pointer)
    if not destination_json:
        return Response({"error": "Invalid question"}, status=400)

    destination = json.loads(destination_json)
    print(destination)
    correct_answer = f"{destination['city']}, {destination['country']}"
    fun_fact = random.choice(destination["trivia"])

    # Fetch user from Redis
    user_key = f"user:{username}"
    correct = int(redis_client.hget(user_key, "correct_answers") or 0)  # ✅ Ensure it's an int
    incorrect = int(redis_client.hget(user_key, "incorrect_answers") or 0)

    # # Update scores
    # if selected_answer == correct_answer:
    #     correct += 1
    #     redis_client.hset(user_key, "correct_answers", str(correct))  # ✅ Store as string
    #     response = {"result": "Correct ✅", "fun_fact": fun_fact}
    # else:
    #     incorrect += 1
    #     redis_client.hset(user_key, "incorrect_answers", str(incorrect)) 
    #     response = {"result": "Incorrect ❌", "fun_fact": fun_fact}

    # # 🔹 Debugging: Print values
    # print(f"Updated Redis: {user_key} - Correct: {correct}, Incorrect: {incorrect}")

    # return Response(response)
    try:
        with transaction.atomic():  # Ensures DB consistency
            user, created = User.objects.get_or_create(username=username)
            
            if selected_answer == correct_answer:
                correct += 1
                user.correct_answers += 1
                response = {"result": "Correct ✅", "fun_fact": fun_fact}
            else:
                incorrect += 1
                user.incorrect_answers += 1
                response = {"result": "Incorrect ❌", "fun_fact": fun_fact}

            # Update Redis
            redis_client.hset(user_key, "correct_answers", str(correct))
            redis_client.hset(user_key, "incorrect_answers", str(incorrect))

            # Save to PostgreSQL
            user.save()

        print(f"Updated {user.username}: Correct: {user.correct_answers}, Incorrect: {user.incorrect_answers}")

    except Exception as e:
        return Response({"error": "Database update failed", "details": str(e)}, status=500)

    return Response(response)


@api_view(["POST"])
def challenge_friend(request):

    authfromheader = request.headers.get("Authorization")
    if not authfromheader:
        authfromheader = request.data.get("token") 
    username = check_token(authfromheader)
    if not username:
        return Response({"error": "Unauthorized"}, status=401)

    inviter_username = username
    invitee_username = request.data.get("invitee_username")

    if not inviter_username or not invitee_username:
        return Response({"error": "Both inviter and invitee usernames are required"}, status=400)

    # Call the register API for the inviter to ensure they are created
    # register_url = reverse('signup')  # Assuming 'register' is the name of the register view
    register_data = {
        'username': invitee_username
    }
    register_response = requests.post(f"http://nginx:80/api/v1/signup", json=register_data, headers={'Content-Type': 'application/json'})

    if register_response.status_code != 200:
        return Response({"error": "Username exists"}, status=register_response.status_code)

    # Fetch the inviter's score from Redis
    inviter_correct = int(redis_client.hget(f"user:{inviter_username}", "correct_answers") or 0)
    inviter_incorrect = int(redis_client.hget(f"user:{inviter_username}", "incorrect_answers") or 0)

    inviter_score = f"Correct: {inviter_correct} | Incorrect: {inviter_incorrect}"

    # Generate invite link with token for the invitee
    invite_token = register_response.json().get("Token")  # Assuming 'Token' is returned in the response
    invite_url = f"http://localhost:80/api/v1/next-question?token={invite_token}"

    # Generate WhatsApp link with the invite message
    invite_message = f"Hey! Join me for a fun travel quiz! My score: {inviter_score}. Let's challenge each other! {invite_url}"
    whatsapp_link = f"https://wa.me/?text={urllib.parse.quote(invite_message)}"

    return Response({
        "message": "Invite link generated successfully",
        "whatsapp_link": whatsapp_link,
        "invite_url": invite_url
    })
