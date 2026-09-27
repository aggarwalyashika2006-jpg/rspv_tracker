# ☁️ Real-Time Cloud Event RSVP Tracker

A **real-time cloud-based event planning and RSVP management platform** that allows organizers to create and manage events while attendees can view events, submit RSVPs, and track event activity.

The application combines a **React frontend**, **FastAPI backend**, **cloud deployment**, authentication, REST APIs, and WebSocket-based real-time communication.

---

## 🌐 Live Demo

🚀 **Live Application:**
https://rspv-tracker.onrender.com/

📂 **GitHub Repository:**
https://github.com/aggarwalyashika2006-jpg/rspv_tracker

---

## 📌 Project Overview

The **Real-Time Cloud Event RSVP Tracker** is designed to simplify event management and attendee response tracking.

Organizers can:

* Create events
* Update event information
* Cancel events
* Manage event capacity
* Monitor attendee responses
* View event analytics
* Send announcements

Attendees can:

* View upcoming events
* Register/login securely
* RSVP to events
* Choose RSVP status
* Cancel their RSVP
* Receive event-related information

The system uses cloud deployment so that the frontend and backend can be accessed through the internet rather than only running locally.

---

## ✨ Features

### 👤 Authentication

* User registration
* User login
* JWT-based authentication
* Protected API endpoints
* Role-based access for organizers and attendees
* Secure password hashing

### 📅 Event Management

* Create new events
* View upcoming events
* Update event details
* Cancel events
* Event status tracking
* Event type classification
* Venue and capacity information

### 🙋 RSVP Management

Users can respond to events using RSVP statuses such as:

* Going
* Maybe
* Not Going

Users can also cancel their RSVP.

### 📊 Event Analytics

Organizers can monitor:

* Total responses
* Going responses
* Maybe responses
* Event participation

### 📢 Announcements

Organizers can create announcements for specific events, while users can retrieve event announcements.

### ⚡ Real-Time Communication

The application uses **WebSockets** to support real-time event activity and communication.

This allows the system to communicate event updates without requiring the user to continuously refresh the page.

### ☁️ Cloud Deployment

The application is deployed using **Render**, allowing the frontend and backend to run as publicly accessible cloud services.

---

## 🏗️ System Architecture

```text
                ┌─────────────────────┐
                │       User          │
                │   Web Browser       │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   React Frontend    │
                │       Vite          │
                └──────────┬──────────┘
                           │
                REST API / WebSocket
                           │
                           ▼
                ┌─────────────────────┐
                │   FastAPI Backend   │
                │      Python         │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    Cloud Database   │
                └─────────────────────┘
```

---

## 🛠️ Technologies Used

### Frontend

* React.js
* Vite
* JavaScript
* HTML
* CSS

### Backend

* Python
* FastAPI
* Uvicorn
* REST APIs
* WebSockets

### Authentication & Security

* JWT
* Password hashing
* Python-Jose
* Passlib / bcrypt
* Email validation

### Database

* Cloud database

### Deployment

* Render
* GitHub

---

## 📁 Project Structure

```text
rspv_tracker/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── api.js
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── requirements.txt
├── README.md
└── ...
```

---

## 🔌 API Functionality

The backend provides APIs for:

| Functionality       | API                                   |
| ------------------- | ------------------------------------- |
| Register            | `POST /api/register`                  |
| Login               | `POST /api/login`                     |
| Current User        | `GET /api/me`                         |
| Get Events          | `GET /api/events`                     |
| Create Event        | `POST /api/events`                    |
| Update Event        | `PUT /api/events/{id}`                |
| Cancel Event        | `DELETE /api/events/{id}`             |
| Submit RSVP         | `POST /api/events/{id}/rsvp`          |
| Cancel RSVP         | `DELETE /api/events/{id}/rsvp`        |
| My RSVPs            | `GET /api/rsvps/me`                   |
| Event Analytics     | `GET /api/events/{id}/analytics`      |
| Create Announcement | `POST /api/events/{id}/announcements` |
| Get Announcements   | `GET /api/events/{id}/announcements`  |
| Notifications       | `GET /api/notifications`              |

### WebSocket

Real-time event communication is supported through:

```text
/ws/events/{event_id}
```

---

## 🔐 Authentication Flow

```text
User
  │
  ▼
Login / Register
  │
  ▼
FastAPI Authentication API
  │
  ▼
JWT Token
  │
  ▼
Token stored by Frontend
  │
  ▼
Authenticated API Requests
```

The frontend sends the JWT token with protected API requests using the `Authorization` header.

---

## ⚡ Real-Time Flow

```text
User Action
     │
     ▼
FastAPI Backend
     │
     ▼
WebSocket Connection
     │
     ▼
Connected Clients
     │
     ▼
Real-Time Update
```

This allows event-related changes to be communicated to connected users without manually refreshing the page.

---

## 🚀 Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/aggarwalyashika2006-jpg/rspv_tracker.git
```

```bash
cd rspv_tracker
```

---

## 🐍 Backend Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## ⚛️ Frontend Setup

Open another terminal and navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

## ☁️ Deployment

The project is deployed using **Render**.

### Frontend

The React/Vite frontend is built using:

```bash
npm install
npm run build
```

### Backend

The FastAPI backend is started using:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Environment variables are configured separately in the cloud deployment environment.

---

## 🔒 Environment Variables

Sensitive values such as secret keys should **not be committed to GitHub**.

Example:

```text
SECRET_KEY=your_secret_key
```

These values should be configured through the deployment platform's environment-variable settings.

---

## 🖥️ Dashboard

The main dashboard provides:

* Total events
* Going responses
* Maybe responses
* Total responses
* Upcoming events
* Event information
* Event status
* Event capacity
* Event location
* Event date and time

---

## 🎯 Project Objectives

The main objectives of this project are:

1. Build a cloud-based event management application.
2. Implement RESTful APIs using FastAPI.
3. Implement secure user authentication.
4. Manage event creation and updates.
5. Implement RSVP functionality.
6. Provide event analytics.
7. Implement real-time communication using WebSockets.
8. Deploy the application to a cloud platform.
9. Connect a modern React frontend with a Python backend.
10. Demonstrate practical cloud computing concepts.

---

## 📚 Cloud Computing Concepts Demonstrated

This project demonstrates practical use of:

* Cloud deployment
* Client-server architecture
* REST APIs
* WebSockets
* Authentication
* Cloud database integration
* Environment variables
* Frontend-backend communication
* Scalable web application architecture
* Real-time data communication

---

## 🔮 Future Enhancements

Possible future improvements include:

* Email notifications
* Calendar integration
* QR-code based event check-in
* Advanced analytics dashboards
* Event search and filtering
* Image upload for events
* Automated reminders
* Admin dashboard
* Push notifications
* Improved real-time notification system

---

## 👩‍💻 Developer

**Yashika Aggarwal**

B.Tech Computer Science & Technology
Maharaja Agrasen Institute of Technology

---

## 🔗 Project Links

🌐 **Live Application:**
https://rspv-tracker.onrender.com/

💻 **GitHub Repository:**
https://github.com/aggarwalyashika2006-jpg/rspv_tracker

---

## ⭐ Project Status

**Status: Completed and Deployed 🚀**

The application is deployed and accessible through the live demo link above.
