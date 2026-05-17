import { io } from "socket.io-client";

// In production, this should point to your backend URL
const URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

export const socket = io(URL, {
  autoConnect: false,
});
