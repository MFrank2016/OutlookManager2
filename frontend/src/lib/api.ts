import axios from "axios";
import { toast } from "sonner";

// Create Axios instance
const api = axios.create({
  baseURL: "/", // Proxy will handle routing to backend
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Add Auth Token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auth_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Helper to format error messages
function getErrorMessage(data: any, error: any): string {
  if (data?.detail) {
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      // Handle Pydantic/FastAPI validation errors (array of objects)
      return data.detail
        .map((err: any) => err.msg || JSON.stringify(err))
        .join(", ");
    }
    if (typeof data.detail === "object") {
      return JSON.stringify(data.detail);
    }
  }
  return error.message || "An error occurred";
}

// Response Interceptor: Handle Errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const data = error.response?.data;

    if (status === 401) {
      // Unauthorized - Clear token and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        
        // Avoid multiple toasts or redirects if already happening
        if (!window.location.pathname.includes("/login")) {
           toast.error("Session expired. Please login again.");
           // Use window.location to force full reload/redirect to clear client state
           window.location.href = "/login"; 
        }
      }
    } else if (status === 403) {
      toast.error("You don't have permission to perform this action.");
    } else {
      // Generic error handling with safe message extraction
      const message = getErrorMessage(data, error);
      
      // Don't show toast for 404s generally unless specific
      if (status !== 404) {
         toast.error(message);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
