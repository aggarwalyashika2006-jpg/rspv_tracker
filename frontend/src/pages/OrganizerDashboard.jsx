import { useEffect, useState } from "react";
import {
  getEvents,
  createEvent,
  updateEvent,
  cancelEvent
} from "../api";

function OrganizerDashboard({ user, onBack }) {
  const [events, setEvents] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const emptyForm = {
    event_name: "",
    description: "",
    event_type: "Workshop",
    event_date: "",
    start_time: "",
    end_time: "",
    venue: "",
    online_link: "",
    maximum_capacity: 100,
    registration_deadline: ""
  };

  const [form, setForm] = useState(emptyForm);

  // =====================================================
  // LOAD EVENTS
  // =====================================================

  const loadEvents = async () => {
    try {
      setLoading(true);

      const data = await getEvents();

      setEvents(data);

      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  // =====================================================
  // FORM CHANGE
  // =====================================================

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((previous) => ({
      ...previous,
      [name]: value
    }));
  };

  // =====================================================
  // CREATE / UPDATE
  // =====================================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    setMessage("");
    setError("");

    try {
      const eventData = {
        ...form,
        maximum_capacity: Number(form.maximum_capacity)
      };

      if (editingEvent) {
        await updateEvent(
          editingEvent.id,
          eventData
        );

        setMessage("Event updated successfully.");
      } else {
        await createEvent(eventData);

        setMessage("Event created successfully.");
      }

      setForm(emptyForm);
      setEditingEvent(null);
      setShowForm(false);

      await loadEvents();

    } catch (err) {
      setError(err.message);
    }
  };

  // =====================================================
  // EDIT
  // =====================================================

  const handleEdit = (event) => {
    setEditingEvent(event);

    setForm({
      event_name: event.event_name || "",
      description: event.description || "",
      event_type: event.event_type || "Workshop",
      event_date: event.event_date || "",
      start_time: event.start_time || "",
      end_time: event.end_time || "",
      venue: event.venue || "",
      online_link: event.online_link || "",
      maximum_capacity: event.maximum_capacity || 100,
      registration_deadline:
        event.registration_deadline || ""
    });

    setShowForm(true);
    setMessage("");
    setError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  };

  // =====================================================
  // DELETE
  // =====================================================

  const handleDelete = async (eventId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this event?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await cancelEvent(eventId);

      setMessage("Event deleted successfully.");

      await loadEvents();

    } catch (err) {
      setError(err.message);
    }
  };

  // =====================================================
  // CANCEL FORM
  // =====================================================

  const closeForm = () => {
    setShowForm(false);
    setEditingEvent(null);
    setForm(emptyForm);
    setError("");
  };

  // =====================================================
  // RENDER
  // =====================================================

  return (
    <div className="organizer-page">

      <div className="dashboard-container">

        {/* HEADER */}

        <div className="dashboard-header">

          <div>
            <p className="badge">
              ORGANIZER DASHBOARD
            </p>

            <h1>
              Welcome, {user.name} 👋
            </h1>

            <p>
              Create and manage your events from one place.
            </p>
          </div>

          <button
            className="back-dashboard-button"
            onClick={onBack}
          >
            ← Events
          </button>

        </div>


        {/* MESSAGE */}

        {message && (
          <div className="success-message">
            {message}
          </div>
        )}

        {error && (
          <div className="dashboard-error">
            {error}
          </div>
        )}


        {/* CREATE BUTTON */}

        {!showForm && (
          <button
            className="create-event-button"
            onClick={() => {
              setShowForm(true);
              setEditingEvent(null);
              setForm(emptyForm);
              setMessage("");
              setError("");
            }}
          >
            + Create New Event
          </button>
        )}


        {/* EVENT FORM */}

        {showForm && (

          <section className="event-form-card">

            <div className="form-header">

              <div>
                <h2>
                  {editingEvent
                    ? "Edit Event"
                    : "Create New Event"}
                </h2>

                <p>
                  Fill in the event details below.
                </p>
              </div>

              <button
                className="close-form-button"
                onClick={closeForm}
              >
                ✕
              </button>

            </div>


            <form onSubmit={handleSubmit}>

              <div className="form-grid">

                <div className="form-group full-width">

                  <label>
                    Event Name
                  </label>

                  <input
                    type="text"
                    name="event_name"
                    value={form.event_name}
                    onChange={handleChange}
                    placeholder="Cloud Computing Workshop"
                    required
                  />

                </div>


                <div className="form-group full-width">

                  <label>
                    Description
                  </label>

                  <textarea
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    placeholder="Describe your event..."
                    rows="4"
                  />

                </div>


                <div className="form-group">

                  <label>
                    Event Type
                  </label>

                  <select
                    name="event_type"
                    value={form.event_type}
                    onChange={handleChange}
                  >
                    <option value="Workshop">
                      Workshop
                    </option>

                    <option value="Seminar">
                      Seminar
                    </option>

                    <option value="Conference">
                      Conference
                    </option>

                    <option value="Hackathon">
                      Hackathon
                    </option>

                    <option value="Webinar">
                      Webinar
                    </option>

                    <option value="Other">
                      Other
                    </option>
                  </select>

                </div>


                <div className="form-group">

                  <label>
                    Maximum Capacity
                  </label>

                  <input
                    type="number"
                    name="maximum_capacity"
                    value={form.maximum_capacity}
                    onChange={handleChange}
                    min="1"
                    required
                  />

                </div>


                <div className="form-group">

                  <label>
                    Event Date
                  </label>

                  <input
                    type="date"
                    name="event_date"
                    value={form.event_date}
                    onChange={handleChange}
                    required
                  />

                </div>


                <div className="form-group">

                  <label>
                    Registration Deadline
                  </label>

                  <input
                    type="datetime-local"
                    name="registration_deadline"
                    value={form.registration_deadline}
                    onChange={handleChange}
                  />

                </div>


                <div className="form-group">

                  <label>
                    Start Time
                  </label>

                  <input
                    type="time"
                    name="start_time"
                    value={form.start_time}
                    onChange={handleChange}
                    required
                  />

                </div>


                <div className="form-group">

                  <label>
                    End Time
                  </label>

                  <input
                    type="time"
                    name="end_time"
                    value={form.end_time}
                    onChange={handleChange}
                    required
                  />

                </div>


                <div className="form-group">

                  <label>
                    Venue
                  </label>

                  <input
                    type="text"
                    name="venue"
                    value={form.venue}
                    onChange={handleChange}
                    placeholder="Computer Science Lab"
                  />

                </div>


                <div className="form-group">

                  <label>
                    Online Link
                  </label>

                  <input
                    type="url"
                    name="online_link"
                    value={form.online_link}
                    onChange={handleChange}
                    placeholder="https://..."
                  />

                </div>

              </div>


              <div className="form-actions">

                <button
                  type="button"
                  className="cancel-form-button"
                  onClick={closeForm}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="save-event-button"
                >
                  {editingEvent
                    ? "Update Event"
                    : "Create Event"}
                </button>

              </div>

            </form>

          </section>

        )}


        {/* EVENTS */}

        <section className="organizer-events">

          <div className="organizer-section-title">

            <div>
              <h2>
                My Events
              </h2>

              <p>
                Manage the events you have created.
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


          {!loading && events.length === 0 && (

            <div className="empty-state">
              <div className="empty-icon">
                📅
              </div>

              <h3>
                No events created yet
              </h3>

              <p>
                Click "Create New Event" to create your first event.
              </p>
            </div>

          )}


          <div className="organizer-event-grid">

            {events.map((event) => (

              <div
                className="organizer-event-card"
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


                <div className="event-actions">

                  <button
                    className="edit-event-button"
                    onClick={() => handleEdit(event)}
                  >
                    ✏️ Edit
                  </button>

                  <button
                    className="delete-event-button"
                    onClick={() =>
                      handleDelete(event.id)
                    }
                  >
                    🗑️ Delete
                  </button>

                </div>

              </div>

            ))}

          </div>

        </section>

      </div>

    </div>
  );
}

export default OrganizerDashboard;