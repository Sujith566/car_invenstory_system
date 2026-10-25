import { useState } from "react";

import {
  apiRequest,
  setAccessToken,
} from "../api/client";

export default function AuthForm({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    const credentials = {
      email: email.trim(),
      password,
    };

    try {
      if (isRegistering) {
        await apiRequest("/auth/register", {
          method: "POST",
          body: credentials,
        });

        // Registration succeeded. Switch to login.
        setIsRegistering(false);
      }

      const login = await apiRequest("/auth/login", {
        method: "POST",
        body: credentials,
      });

      setAccessToken(login.access_token);

      const user = await apiRequest("/auth/me");

      setPassword("");
      onLogin(user);
    } catch (error) {
      setAccessToken("");
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  function switchMode() {
    setIsRegistering((previous) => !previous);
    setPassword("");
    setError("");
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-700">
          Car Inventory
        </p>

        <h1 className="mt-3 text-3xl font-bold">
          {isRegistering ? "Create an account" : "Welcome back"}
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          {isRegistering
            ? "Register to browse and purchase vehicles."
            : "Sign in to your inventory workspace."}
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium"
            >
              Email address
            </label>

            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              maxLength={254}
              value={email}
              disabled={busy}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-300 p-3 focus:outline-emerald-600"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              autoComplete={
                isRegistering ? "new-password" : "current-password"
              }
              required
              minLength={8}
              maxLength={128}
              value={password}
              disabled={busy}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-300 p-3 focus:outline-emerald-600"
            />
          </div>

          {error && (
            <p
              role="alert"
              className="rounded-lg bg-red-50 p-3 text-sm text-red-700"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-emerald-700 p-3 font-semibold text-white hover:bg-emerald-800 disabled:opacity-50"
          >
            {busy
              ? "Please wait..."
              : isRegistering
                ? "Create account"
                : "Sign in"}
          </button>
        </form>

        <button
          type="button"
          onClick={switchMode}
          disabled={busy}
          className="mt-6 w-full text-sm font-medium text-emerald-700 disabled:opacity-50"
        >
          {isRegistering
            ? "Already registered? Sign in"
            : "New here? Create an account"}
        </button>
      </section>
    </main>
  );
}