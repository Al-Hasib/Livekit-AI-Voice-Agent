import { useState, useCallback } from "react";
import { useLiveKitRoom } from "./useLiveKitRoom";
import { useAgentStore } from "../store/agentStore";

export function useAgentConnection() {
  const { connect, disconnect, toggleMute } = useLiveKitRoom();
  const { connected, connecting, muted, error } = useAgentStore();
  const [roomInput, setRoomInput] = useState(() =>
    `room-${Math.random().toString(36).slice(2, 8)}`
  );
  const [nameInput, setNameInput] = useState(() =>
    `user-${Math.random().toString(36).slice(2, 6)}`
  );

  const handleConnect = useCallback(async () => {
    if (!roomInput.trim() || !nameInput.trim()) return;
    await connect(nameInput.trim(), roomInput.trim());
  }, [connect, nameInput, roomInput]);

  const handleDisconnect = useCallback(async () => {
    await disconnect();
  }, [disconnect]);

  return {
    connected,
    connecting,
    muted,
    error,
    roomInput,
    setRoomInput,
    nameInput,
    setNameInput,
    handleConnect,
    handleDisconnect,
    toggleMute,
  };
}