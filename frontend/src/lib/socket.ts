import { io } from "socket.io-client";

// By omitting the URL, Socket.io defaults to the current domain (Vercel)
// Vercel's proxy rewrites will then forward the request to the EC2 backend
export const socket = io({
  path: "/socket.io/",
  autoConnect: false,
  transports: ['polling', 'websocket']
});
