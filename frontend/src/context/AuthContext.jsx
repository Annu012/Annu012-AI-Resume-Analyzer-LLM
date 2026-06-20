import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { loginRecruiter, registerRecruiter } from "../api/client";

const AuthContext = createContext(null);

function decodeEmailFromToken(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("ara_token"));
  const [email, setEmail] = useState(() => {
    const existing = localStorage.getItem("ara_token");
    return existing ? decodeEmailFromToken(existing) : null;
  });

  useEffect(() => {
    if (token) {
      localStorage.setItem("ara_token", token);
      setEmail(decodeEmailFromToken(token));
    } else {
      localStorage.removeItem("ara_token");
      setEmail(null);
    }
  }, [token]);

  const login = useCallback(async (credentials) => {
    const data = await loginRecruiter(credentials);
    setToken(data.access_token);
    return data;
  }, []);

  const register = useCallback(async (payload) => {
    await registerRecruiter(payload);
    // auto-login right after successful registration
    const data = await loginRecruiter({ email: payload.email, password: payload.password });
    setToken(data.access_token);
    return data;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
  }, []);

  const value = {
    token,
    email,
    isAuthenticated: Boolean(token),
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
