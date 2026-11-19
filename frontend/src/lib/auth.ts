const BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const TOKEN_KEY = "ares_operator_token";

export const auth = {
  token(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  },

  isLoggedIn(): boolean {
    return Boolean(this.token());
  },

  async login(token: string): Promise<boolean> {
    const cleaned = token.trim();

    if (!cleaned) {
      return false;
    }

    try {
      const response = await fetch(
        `${BASE_URL}/auth/check`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${cleaned}`,
          },
        }
      );

      if (!response.ok) {
        return false;
      }

      sessionStorage.setItem(
        TOKEN_KEY,
        cleaned
      );

      return true;
    } catch (error) {
      console.error(
        "Authentication failed:",
        error
      );

      return false;
    }
  },

  logout(): void {
    sessionStorage.removeItem(TOKEN_KEY);
  },
};