import React from "react";
import { Mic, MicOff, Phone, PhoneOff } from "lucide-react";
import { useAgentConnection } from "../hooks/useAgentConnection";

export const AgentControls: React.FC = () => {
  const {
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
  } = useAgentConnection();

  return (
    <div className="space-y-4">
      {/* Connection Form */}
      {!connected && (
        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Your Name</label>
            <input
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white"
              placeholder="Enter your name"
              disabled={connecting}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Room Name</label>
            <input
              type="text"
              value={roomInput}
              onChange={(e) => setRoomInput(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white"
              placeholder="Enter room name"
              disabled={connecting}
            />
          </div>
          <button
            onClick={handleConnect}
            disabled={connecting || !nameInput.trim() || !roomInput.trim()}
            className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg px-4 py-3 font-medium transition-colors"
          >
            <Phone size={20} />
            {connecting ? "Connecting..." : "Connect"}
          </button>
        </div>
      )}

      {/* Connected Controls */}
      {connected && (
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={toggleMute}
            className={`p-4 rounded-full transition-colors ${
              muted
                ? "bg-red-600 hover:bg-red-700"
                : "bg-gray-700 hover:bg-gray-600"
            }`}
            title={muted ? "Unmute" : "Mute"}
          >
            {muted ? <MicOff size={24} /> : <Mic size={24} />}
          </button>

          <button
            onClick={handleDisconnect}
            className="p-4 rounded-full bg-red-600 hover:bg-red-700 transition-colors"
            title="Disconnect"
          >
            <PhoneOff size={24} />
          </button>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg px-4 py-2 text-red-200 text-sm">
          {error}
        </div>
      )}
    </div>
  );
};