import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { auth } from "@/lib/auth";

export default function LoginForm() {
  const navigate = useNavigate();

  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const success = await auth.login(token);

      if (!success) {
        setError(
          "Invalid operator token or backend unavailable."
        );
        return;
      }

      navigate("/", { replace: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-100 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-2">
          ARES Operator Login
        </h1>

        <p className="text-sm text-gray-500 mb-6">
          Agentic Secure Smart Agriculture Rover
        </p>

        <form
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium mb-2">
              Operator Token
            </label>

            <input
              type="password"
              value={token}
              onChange={(event) =>
                setToken(event.target.value)
              }
              className="w-full border rounded-lg px-4 py-3"
              placeholder="Enter backend operator token"
              autoComplete="off"
              required
            />
          </div>

          {error && (
            <p
              role="alert"
              className="text-red-600 text-sm"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white rounded-lg py-3 font-semibold"
          >
            {loading
              ? "Verifying..."
              : "Login to ARES"}
          </button>
        </form>

        <p className="text-xs text-gray-500 mt-5">
          Local development access. All protected API
          requests are verified by the backend.
        </p>
      </div>
    </div>
  );
}