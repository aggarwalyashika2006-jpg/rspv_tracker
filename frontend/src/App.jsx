import { useEffect, useState } from "react";
import "./App.css";
import { getEvents } from "./api";

import Login from "./pages/Login";
import OrganizerDashboard from "./pages/OrganizerDashboard";
import {
  getEvents,
  getToken,
  logout
} from "./api";

function App() {

  const [events, setEvents] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const [currentPage, setCurrentPage] = useState(
    getToken() ? "dashboard" : "dashboard"
  );

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");

    return savedUser
      ? JSON.parse(savedUser)
      : null;
  });


  // =====================================================
  // LOAD EVENTS
  // =====================================================

 const loadEvents = async () => {
  try {
    setLoading(true);

    const data = await getEvents();

    setEvents(data);
    setMessage("");

  } catch (error) {

    console.error(error);

    setMessage(
      "Could not connect to the backend. Make sure FastAPI is running."
    );

  } finally {

    setLoading(false);
  }
};


  useEffect(() => {

    loadEvents();

  }, []);


  // =====================================================
  // LOGIN
  // =====================================================

  const handleLogin = (loggedInUser) => {

    setUser(loggedInUser);

    setCurrentPage("dashboard");

  };


  // =====================================================
  // LOGOUT
  // =====================================================

  const handleLogout = () => {

    logout();

    setUser(null);

    setCurrentPage("dashboard");

  };

// =====================================================
// ORGANIZER DASHBOARD
// =====================================================

if (
  currentPage === "organizer" &&
  user &&
  user.role === "ORGANIZER"
) {
  return (
    <OrganizerDashboard
      user={user}
      onBack={() => setCurrentPage("dashboard")}
    />
  );
}
  // =====================================================
  // LOGIN PAGE
  // =====================================================

  if (currentPage === "login") {

    return (
      <Login
        onLogin={handleLogin}
        onBack={() => setCurrentPage("dashboard")}
      />
    );

  }


  // =====================================================
  // DASHBOARD
  // =====================================================

  return (

    <div className="app">

      {/* NAVBAR */}

      <nav className="navbar">

        <div className="logo">
          ☁️ CloudEvent
        </div>


        <div className="nav-links">

          <span
            onClick={() => setCurrentPage("dashboard")}
          >
            Events
          </span>

          <span
            onClick={() => setCurrentPage("dashboard")}
          >
            Dashboard
          </span>


          {user ? (

            <>
              <span className="user-name">
                👤 {user.name}
              </span>

              <button
                className="nav-logout"
                onClick={handleLogout}
              >
                Logout
              </button>
            </>

          ) : (

            <button
              className="nav-login"
              onClick={() => setCurrentPage("login")}
            >
              Login
            </button>

          )}

        </div>

      </nav>


      {/* MAIN */}

      <main className="container">


        {/* HERO */}

        <section className="hero">

          <div>

            <p className="badge">
              REAL-TIME CLOUD PLATFORM
            </p>

            <h1>
              Event Planning &
              <span> RSVP Tracker</span>
            </h1>

            <p className="hero-text">
              Create events, manage attendees,
              track RSVPs, and monitor event
              activity in real time.
            </p>

          </div>


          <div className="cloud-card">

            <div className="cloud-icon">
              ☁️
            </div>

            <h3>
              Cloud Connected
            </h3>

            <p>
              FastAPI + React + Cloud Database
            </p>

          </div>

        </section>


        {/* STATISTICS */}

        <section className="stats">

          <div className="stat-card">

            <h2>
              {events.length}
            </h2>

            <p>
              Total Events
            </p>

          </div>


          <div className="stat-card">

            <h2>
              0
            </h2>

            <p>
              Going
            </p>

          </div>


          <div className="stat-card">

            <h2>
              0
            </h2>

            <p>
              Maybe
            </p>

          </div>


          <div className="stat-card">

            <h2>
              0
            </h2>

            <p>
              Responses
            </p>

          </div>

        </section>


        {/* EVENTS */}

        <section className="events-section">


          <div className="section-header">

            <div>

              <h2>
                Upcoming Events
              </h2>

              <p>
                Discover and RSVP to upcoming events.
              </p>

            </div>


            <button
              className="refresh-button"
              onClick={loadEvents}
            >
              🔄 Refresh
            </button>

          </div>


          {loading && (

            <div className="loading">
              Loading events...
            </div>

          )}


          {message && (

            <div className="error-message">
              {message}
            </div>

          )}


          {!loading &&
            !message &&
            events.length === 0 && (

              <div className="empty-state">

                <div className="empty-icon">
                  📅
                </div>

                <h3>
                  No events yet
                </h3>

                <p>
                  Events created by organizers
                  will appear here.
                </p>

              </div>

            )}


          <div className="event-grid">

            {events.map((event) => (

              <div
                className="event-card"
                key={event.id}
              >

                <div className="event-header">

                  <span className="event-type">
                    {event.event_type}
                  </span>

                  <span className="event-status">
                    {event.status}
                  </span>

                </div>


                <h3>
                  {event.event_name}
                </h3>


                <p className="description">

                  {event.description ||
                    "No description available."}

                </p>


                <div className="event-info">

                  <p>
                    📅 {event.event_date}
                  </p>

                  <p>
                    🕐 {event.start_time}
                    {" - "}
                    {event.end_time}
                  </p>

                  <p>
                    📍 {event.venue || "Online"}
                  </p>

                  <p>
                    👥 Capacity:
                    {" "}
                    {event.maximum_capacity}
                  </p>

                </div>


                <button
                  className="rsvp-button"
                  onClick={() => {
                    if (!user) {
                      setCurrentPage("login");
                    }
                  }}
                >
                  {user ? "View Event" : "Login to RSVP"}
                </button>

              </div>

            ))}

          </div>

        </section>

      </main>


      {/* FOOTER */}

      <footer>

        <p>
          Real-Time Cloud-Based Event
          Planning & RSVP Tracker
        </p>

        <p>
          Cloud Computing Project
        </p>

      </footer>

    </div>

  );
}

export default App;