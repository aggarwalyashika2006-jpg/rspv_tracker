import { useState } from "react";
import { register } from "../api";
import "./Auth.css";

function Register({ onRegister, onBack }) {

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("ATTENDEE");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (e) => {

    e.preventDefault();

    setError("");
    setSuccess("");

    if (!name || !email || !password) {
      setError(
        "Please fill in all required fields."
      );
      return;
    }

    if (password.length < 6) {
      setError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    try {

      setLoading(true);

      await register(
        name,
        email,
        password,
        role
      );

      setSuccess(
        "Registration successful! You can now login."
      );

      setName("");
      setEmail("");
      setPassword("");

      setTimeout(() => {
        onRegister();
      }, 1200);

    } catch (err) {

      setError(
        err.message ||
        "Registration failed."
      );

    } finally {

      setLoading(false);

    }
  };

  return (
    <div className="auth-page">

      <div className="auth-card">

        <button
          className="back-button"
          onClick={onBack}
        >
          ← Back to Events
        </button>

        <div className="auth-logo">
          ☁️
        </div>

        <h1>Create Account</h1>

        <p className="auth-subtitle">
          Join CloudEvent and start managing events.
        </p>

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        {success && (
          <div className="auth-success">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          <label>
            Full Name
          </label>

          <input
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(e) =>
              setName(e.target.value)
            }
          />

          <label>
            Email Address
          </label>

          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) =>
              setEmail(e.target.value)
            }
          />

          <label>
            Password
          </label>

          <input
            type="password"
            placeholder="Minimum 6 characters"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
          />

          <label>
            Account Type
          </label>

          <select
            value={role}
            onChange={(e) =>
              setRole(e.target.value)
            }
          >
            <option value="ATTENDEE">
              Attendee
            </option>

            <option value="ORGANIZER">
              Organizer
            </option>
          </select>

          <button
            className="auth-submit"
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Creating Account..."
              : "Create Account"}
          </button>

        </form>

        <p className="auth-switch">
          Already have an account?
        </p>

        <button
          className="secondary-auth-button"
          onClick={() =>
            window.dispatchEvent(
              new CustomEvent("show-login")
            )
          }
        >
          Login
        </button>

      </div>

    </div>
  );
}

export default Register;