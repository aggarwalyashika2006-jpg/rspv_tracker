const API_URL = "https://real-time-cloud-event-rsvp-tracker-tas4.onrender.com";

// ============================================================
// TOKEN
// ============================================================

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export function getUser() {
  const user = localStorage.getItem("user");

  if (!user) {
    return null;
  }

  try {
    return JSON.parse(user);
  } catch {
    return null;
  }
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}


// ============================================================
// GENERAL REQUEST
// ============================================================

async function request(endpoint, options = {}) {

  const token = getToken();

  const headers = {
    ...(options.body instanceof FormData
      ? {}
      : {
          "Content-Type": "application/json"
        }),

    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      ...options,
      headers
    }
  );

  let data;

  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(
      data.detail || "Something went wrong."
    );
  }

  return data;
}


// ============================================================
// REGISTER
// ============================================================

export async function register(
  name,
  email,
  password,
  role
) {

  return request(
    "/api/register",
    {
      method: "POST",

      body: JSON.stringify({
        name,
        email,
        password,
        role
      })
    }
  );
}


// ============================================================
// LOGIN
// ============================================================

export async function login(
  email,
  password
) {

  const formData = new URLSearchParams();

  formData.append(
    "username",
    email
  );

  formData.append(
    "password",
    password
  );

  const response = await fetch(
    `${API_URL}/api/login`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded"
      },

      body: formData
    }
  );

  const data = await response.json();

  if (!response.ok) {

    throw new Error(
      data.detail || "Login failed."
    );
  }

  setToken(
    data.access_token
  );

  localStorage.setItem(
    "user",
    JSON.stringify(data.user)
  );

  return data;
}


// ============================================================
// CURRENT USER
// ============================================================

export async function getMe() {

  return request(
    "/api/me"
  );
}


// ============================================================
// EVENTS
// ============================================================

export async function getEvents() {

  return request(
    "/api/events"
  );
}


export async function getEvent(
  eventId
) {

  return request(
    `/api/events/${eventId}`
  );
}


export async function createEvent(
  event
) {

  return request(
    "/api/events",
    {
      method: "POST",
      body: JSON.stringify(event)
    }
  );
}


export async function updateEvent(
  eventId,
  event
) {

  return request(
    `/api/events/${eventId}`,
    {
      method: "PUT",
      body: JSON.stringify(event)
    }
  );
}


export async function deleteEvent(
  eventId
) {

  return request(
    `/api/events/${eventId}`,
    {
      method: "DELETE"
    }
  );
}


// ============================================================
// RSVP
// ============================================================

export async function submitRSVP(
  eventId,
  status
) {

  return request(
    `/api/events/${eventId}/rsvp`,
    {
      method: "POST",

      body: JSON.stringify({
        status
      })
    }
  );
}


export async function getMyRSVPs() {

  return request(
    "/api/rsvps/me"
  );
}


// ============================================================
// ORGANIZER ANALYTICS
// ============================================================

export async function getEventRSVPs(
  eventId
) {

  return request(
    `/api/events/${eventId}/rsvps`
  );
}


export async function getAnalytics(
  eventId
) {

  return request(
    `/api/events/${eventId}/analytics`
  );
}


// ============================================================
// ANNOUNCEMENTS
// ============================================================

export async function createAnnouncement(
  eventId,
  title,
  message
) {

  return request(
    `/api/events/${eventId}/announcements`,
    {
      method: "POST",

      body: JSON.stringify({
        title,
        message
      })
    }
  );
}


export async function getAnnouncements(
  eventId
) {

  return request(
    `/api/events/${eventId}/announcements`
  );
}


// ============================================================
// NOTIFICATIONS
// ============================================================

export async function getNotifications() {

  return request(
    "/api/notifications"
  );
}


export async function markNotificationRead(
  notificationId
) {

  return request(
    `/api/notifications/${notificationId}/read`,
    {
      method: "PUT"
    }
  );
}


// ============================================================
// WEBSOCKET
// ============================================================

export function createWebSocket(
  eventId,
  onMessage
) {

  const websocket =
    new WebSocket(
      wss://real-time-cloud-event-rsvp-tracker-tas4.onrender.com
    );

  websocket.onopen = () => {

    console.log(
      `WebSocket connected for event ${eventId}`
    );
  };

  websocket.onmessage = (
    event
  ) => {

    try {

      const data =
        JSON.parse(
          event.data
        );

      onMessage(data);

    } catch (error) {

      console.error(
        "WebSocket message error:",
        error
      );
    }
  };

  websocket.onerror = (
    error
  ) => {

    console.error(
      "WebSocket error:",
      error
    );
  };

  websocket.onclose = () => {

    console.log(
      `WebSocket disconnected for event ${eventId}`
    );
  };

  return websocket;
}
