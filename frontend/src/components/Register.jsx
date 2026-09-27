import { useState } from "react";
import { register } from "../api";

function Register({
  onRegister,
  onSwitchToLogin
}) {

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("ATTENDEE");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {

    event.preventDefault();

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

      const data = await register(
        name,
        email,
        password,
        role
      );

      setSuccess(
        "Registration successful! You can now login."
      );

      setTimeout(() => {

        onRegister();

      }, 1000);

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Registration failed."
      );

    } finally {

      setLoading(false);

    }
  };

  return (
    <div className="auth-page">

      <div className="auth-card">

        <div className="auth-icon">
          ☁️
        </div>

        <h1>
          Create Account
        </h1>

        <p className="auth-subtitle">
          Join CloudEvent
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

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >

          <label>
            Full Name
          </label>

          <input
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(event) =>
              setName(event.target.value)
            }
          />

          <label>
            Email
          </label>

          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
          />

          <label>
            Password
          </label>

          <input
            type="password"
            placeholder="Minimum 6 characters"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
          />

          <label>
            Account Type
          </label>

          <select
            value={role}
            onChange={(event) =>
              setRole(event.target.value)
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
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading
              ? "Creating Account..."
              : "Create Account"}
          </button>

        </form>

        <div className="auth-switch">

          <span>
            Already have an account?
          </span>

          <button
            type="button"
            onClick={onSwitchToLogin}
          >
            Login
          </button>

        </div>

      </div>

    </div>
  );
}

export default Register;