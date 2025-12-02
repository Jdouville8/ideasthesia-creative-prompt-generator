import axios from 'axios';
import { logoutUser } from '../store/authSlice';

// Create axios instance
const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
});

// Store reference for logout dispatch
let store;

export const setStore = (storeInstance) => {
  store = storeInstance;
};

// Track if we've already shown the session expired alert
let sessionExpiredAlertShown = false;

// Response interceptor to handle auth errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if error is due to authentication (401 or 403)
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      // Clear token and user data
      localStorage.removeItem('token');
      localStorage.removeItem('user');

      // Dispatch logout action if store is available
      if (store) {
        store.dispatch(logoutUser());
      }

      // Show user-friendly message (only once per page load)
      if (!sessionExpiredAlertShown) {
        sessionExpiredAlertShown = true;
        alert('Your session has expired. Please log in again to continue.');
        // Reset the flag after a short delay to allow re-showing if needed
        setTimeout(() => {
          sessionExpiredAlertShown = false;
        }, 5000);
      }

      console.warn('Session expired - user logged out automatically');
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
