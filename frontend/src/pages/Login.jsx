import { useState } from "react";
import { login } from "../api";
import "./Auth.css";

function Login({ onLogin, onBack }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);

      const data = await login(
        email,
        password
      );

      onLogin(data.user);

    } catch (err) {
      setError(
        err.message ||
        "Login failed. Please check your credentials."
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

        <h1>Welcome Back</h1>

        <p className="auth-subtitle">
          Login to manage your events and RSVPs.
        </p>

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>

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
            placeholder="Enter your password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
          />

          <button
            className="auth-submit"
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Logging in..."
              : "Login"}
          </button>

        </form>

        <p className="auth-switch">
          Don't have an account?
        </p>

        <button
          className="secondary-auth-button"
          onClick={() =>
            window.dispatchEvent(
              new CustomEvent("show-register")
            )
          }
        >
          Create Account
        </button>

      </div>

    </div>
  );
}

export default Login;