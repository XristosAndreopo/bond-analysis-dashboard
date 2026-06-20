/**
 * Central Axios API client.
 *
 * All backend requests should go through this file so authentication headers,
 * base URL, and future error handling remain centralized.
 */

import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000/api";

/**
 * Axios instance configured for the Django REST API.
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Attach the JWT access token to every request if it exists.
 */
apiClient.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem("accessToken");

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export default apiClient;