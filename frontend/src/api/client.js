import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE_URL });

// Attach the JWT (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ara_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function registerRecruiter({ email, password, companyName }) {
  const { data } = await api.post("/register", {
    email,
    password,
    company_name: companyName || null,
  });
  return data;
}

export async function loginRecruiter({ email, password }) {
  const { data } = await api.post("/login", { email, password });
  return data;
}

export async function analyzeResume({ file, jobDescription, jobTitle }) {
  const form = new FormData();
  form.append("file", file);
  form.append("job_description", jobDescription);
  form.append("job_title", jobTitle || "");
  const { data } = await api.post("/analyze-pdf", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function fetchDashboard() {
  const { data } = await api.get("/dashboard");
  return data;
}

export async function checkHealth() {
  const { data } = await api.get("/health");
  return data;
}

export default api;
