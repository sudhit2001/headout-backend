# **Travel Quiz Game Backend**

## **Project Overview**

The **Travel Quiz Game** backend is a Django-based web application that allows users to participate in a travel-themed quiz game. Users are presented with multiple-choice questions about travel destinations, and the backend handles game logic, user authentication, and data management. This project integrates multiple technologies such as **JWT** for secure authentication, **Redis** for caching, and **MongoDB** for storing travel destinations. The entire application is containerized using **Docker**, providing an isolated and easily deployable environment.

## **Tech Stack**

### **Backend Framework**
- **Django**: A high-level Python web framework that encourages rapid development and clean, pragmatic design. It's used to build the core logic of the quiz game, including user authentication, game mechanics, and API endpoints.

### **Database**
- **MongoDB**: A NoSQL database used to store travel destinations and associated trivia. It allows for flexible data structures, which is useful for handling various destination facts.
- **PostgreSQL**: A relational database used for storing user scores (correct and incorrect answers). PostgreSQL is used because of its ability to handle complex queries and ensure data integrity.

### **Caching**
- **Redis**: An in-memory key-value store used to cache travel destination data and track user scores, making the app faster by reducing database hits.

### **Authentication**
- **JWT (JSON Web Tokens)**: Used for secure user authentication and to validate user requests. JWT provides a stateless method of handling authentication by including a token in the request headers.

### **Containerization**
- **Docker**: Used for containerizing the entire backend application along with its dependencies, ensuring consistency across environments.
- **Docker Compose**: Used to manage multi-container Docker applications, defining the app services (Django, Redis, MongoDB, PostgreSQL) in a `docker-compose.yml` file.

### **Other Technologies**
- **Nginx**: (Optional) Reverse proxy server that can be added to handle incoming HTTP requests and direct them to appropriate services.

## **Features**

- **User Authentication**:
  - **Sign Up**: Users can register with a unique username. JWT tokens are issued upon registration.
  - **Login**: Users can log in with their username and receive a JWT token for subsequent requests.

- **Quiz Game Mechanics**:
  - **Random Quiz Questions**: The game fetches random travel destinations stored in MongoDB and presents them with multiple-choice options.
  - **Answer Feedback**: After each answer, users receive feedback, including whether they were correct or incorrect, along with a fun fact.
  - **Score Tracking**: User scores (correct and incorrect answers) are tracked in both PostgreSQL and Redis.
  - **Next Question**: The game provides a "Next Question" button that fetches the next quiz question and updates the score.

- **User Interaction**:
  - **Challenge Friends**: Users can generate an invite link to challenge their friends, which contains the JWT token.
  - **Leaderboard**: Users' scores are tracked and can be shared.

## **Setup and Installation**

### **Prerequisites**

Before setting up the project, ensure you have the following tools installed:

- **Docker** and **Docker Compose**: For containerization and easy setup.
- **Python 3.11+**: For local development without Docker.
- **Redis**: In-memory data store for caching.
- **MongoDB**: For storing travel destinations.
- **PostgreSQL**: For storing user scores.


## Project Structure

```
Globetrotter/
|-- docker-compose.yml
|-- .env
|-- Globetrotter/quiz
|-- nginx/
    |-- default.conf
|-- docker/
    |-- django.dockerfile
    |-- nginx.dockerfile
```

## Setup Instructions

### 1. Clone the Repository

```sh
git clone <repository-url>
cd Globetrotter
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and define the following variables:

```env
# PostgreSQL
POSTGRES_DB=globetrotter_db
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_pass

# MongoDB
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=globetrotter_mongo
MONGO_DB_ROOT_USERNAME=mongo_user
MONGO_DB_ROOT_PASSWORD=mongo_pass

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3. Build and Start the Services

```sh
docker-compose up --build -d
```

This starts the following services:

- **Django Backend** (2 containers)
- **PostgreSQL** (stores user scores)
- **MongoDB** (stores destinations and quiz questions)
- **Redis** (caching and session management)
- **Nginx** (reverse proxy)

### 4. Apply Migrations and Create Superuser

```sh
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py createsuperuser
```

### 5. Populate MongoDB with Destination Data (Optional)

If MongoDB is empty, you can seed it with quiz data:

```sh
docker-compose exec django python populate_db.py
```

### 6. Access the Application

- **Django API**: [http://localhost:8000/](http://localhost:8000/)
- **Admin Panel**: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- **Nginx (Proxy)**: [http://localhost/](http://localhost/)


### 7. Stopping and Removing Containers

```sh
docker-compose down
```

### API Endpoints

#### Authentication
- `POST /api/v1/signup/` - Register a new user (JWT-based authentication)
- `POST /api/v1/login/` - Log in and receive a JWT token
- `GET /api/v1/check/` - Validate a JWT token

#### Quiz Game
- `GET /api/v1/next_question/` - Retrieve the next quiz question
- `POST /api/v1/submit_answer/` - Submit an answer and get immediate feedback

#### Social & Invites
- `POST /api/v1/challenge_friend/` - Generate an invite link for a friend
- `POST /api/v1/invite/` - Store an invitee's quiz score and generate a challenge link


## Notes

- The `runserver` command is used for development.
- The backend retrieves destinations from Redis instead of MongoDB for better performance.
- A global pointer in Redis ensures unique, round-robin quiz question selection.

## Contributing

Feel free to submit issues and pull requests to improve the project.

## License

MIT License

