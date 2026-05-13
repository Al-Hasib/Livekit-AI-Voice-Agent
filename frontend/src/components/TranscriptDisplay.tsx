import React, { useEffect, useRef } from "react";
import { useAgentStore } from "../store/agentStore";

export const TranscriptDisplay: React.FC = () => {
  const transcripts = useAgentStore((s) => s.transcripts);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcripts]);

  if (transcripts.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-500">
        <p>Conversation transcript will appear here...</p>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="h-64 overflow-y-auto space-y-3 p-3">
      {transcripts.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-2 ${
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-gray-700 text-gray-100"
            }`}
          >
            <p className="text-sm">{msg.content}</p>
            <span className="text-xs opacity-60">
              {msg.role === "user" ? "You" : "Agent"} ·{" "}
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};