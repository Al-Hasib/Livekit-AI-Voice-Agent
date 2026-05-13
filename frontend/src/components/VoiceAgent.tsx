import React from "react";
import { AudioVisualizer } from "./AudioVisualizer";
import { AgentControls } from "./AgentControls";
import { TranscriptDisplay } from "./TranscriptDisplay";
import { DocumentUpload } from "./DocumentUpload";
import { useAgentStore } from "../store/agentStore";

export const VoiceAgent: React.FC = () => {
  const connected = useAgentStore((s) => s.connected);
  const speaking = useAgentStore((s) => s.speaking);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            AI Voice Agent
          </h1>
          <p className="text-gray-500 mt-1">
            Real-time voice conversation with RAG-powered knowledge
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Agent Controls + Visualizer */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4">Controls</h2>
              <AgentControls />
            </div>

            {connected && (
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
                <h2 className="text-lg font-semibold mb-4">Audio</h2>
                <div className="flex justify-center">
                  <div
                    className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                      speaking
                        ? "bg-green-600/30 shadow-lg shadow-green-500/20 scale-110"
                        : "bg-gray-800 scale-100"
                    }`}
                  >
                    <div
                      className={`w-16 h-16 rounded-full transition-all duration-300 ${
                        speaking
                          ? "bg-green-500 animate-pulse"
                          : "bg-gray-700"
                      }`}
                    />
                  </div>
                </div>
                <div className="mt-4">
                  <AudioVisualizer />
                </div>
              </div>
            )}
          </div>

          {/* Center: Transcript */}
          <div className="lg:col-span-1">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 h-full">
              <h2 className="text-lg font-semibold mb-4">Conversation</h2>
              <TranscriptDisplay />
            </div>
          </div>

          {/* Right: Documents */}
          <div className="lg:col-span-1">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 h-full">
              <DocumentUpload />
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div className="mt-6 flex items-center justify-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                connected ? "bg-green-500" : "bg-gray-600"
              }`}
            />
            <span>{connected ? "Connected" : "Disconnected"}</span>
          </div>
          {connected && (
            <span>· Powered by LiveKit + RAG</span>
          )}
        </div>
      </div>
    </div>
  );
};