import { useState, useEffect } from "react";

const PICO_IP = "192.168.4.1"; // change if needed

export function useWebSocket(setScore, setInstructionIndex, setCurrentCommand) {
  const [ws, setWs] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false); // Track connection state

  useEffect(() => {
    const connectWebSocket = () => {
      const socket = new WebSocket(`ws://${PICO_IP}/connect-websocket`);

      socket.onopen = () => {
        console.log("✅ WebSocket connected");
        setWs(socket);
        setIsConnected(true); // Mark as connected
      };

      socket.onmessage = (event) => {
        console.log("📥 Received from Pico:", event.data);
        setMessages((prev) => [...prev, event.data]); // Store received messages

        if (event.data === "green tower") {
          console.log("🎯 Updating score +50");
          setScore((prevScore) => prevScore + 50);
        } else if (event.data.startsWith("route_index:")) {
          // Parse the route_index message
          const parts = event.data.split(":");
          if (parts.length >= 3) {
            const index = parseInt(parts[1], 10);
            const command = parts[2];
            
            if (!isNaN(index) && setInstructionIndex) {
              console.log(`🤖 Executing command: ${command} (index: ${index})`);
              setInstructionIndex(index);
              
              if (setCurrentCommand) {
                setCurrentCommand(command);
              }
            } else {
              console.error("⚠️ Invalid route index:", parts[1]);
            }
          } else {
            console.error("⚠️ Malformed route_index message:", event.data);
          }
        }
      };

      socket.onclose = () => {
        console.log("❌ WebSocket closed");
        if (isConnected) {
          console.error("⚠️ WebSocket disconnected unexpectedly");
        }
        setIsConnected(false); // Mark as disconnected
      };

      socket.onerror = (error) => {
        console.error("⚠️ WebSocket Error:", error);
      };

      return socket;
    };

    const socket = connectWebSocket();

    return () => {
      socket.close();
    };
  }, []);

  const sendCommand = (command) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      console.log("📤 Sending command:", command);
      ws.send(command);
    } else {
      console.error("⚠️ WebSocket not connected");
    }
  };

  return { sendCommand, messages, ws, isConnected };
}