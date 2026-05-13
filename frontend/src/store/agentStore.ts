import { create } from "zustand";
import type { TranscriptMessage, AgentState } from "../types";

interface AgentActions {
  setConnected: (connected: boolean) => void;
  setConnecting: (connecting: boolean) => void;
  setMuted: (muted: boolean) => void;
  setSpeaking: (speaking: boolean) => void;
  setRoomName: (roomName: string) => void;
  setIdentity: (identity: string) => void;
  setAudioLevel: (level: number) => void;
  setError: (error: string | null) => void;
  addTranscript: (message: TranscriptMessage) => void;
  clearTranscripts: () => void;
  reset: () => void;
}

const initialState: AgentState = {
  connected: false,
  connecting: false,
  muted: false,
  speaking: false,
  roomName: "",
  identity: "",
  transcripts: [],
  audioLevel: 0,
  error: null,
};

export const useAgentStore = create<AgentState & AgentActions>()((set) => ({
  ...initialState,

  setConnected: (connected) => set({ connected }),
  setConnecting: (connecting) => set({ connecting }),
  setMuted: (muted) => set({ muted }),
  setSpeaking: (speaking) => set({ speaking }),
  setRoomName: (roomName) => set({ roomName }),
  setIdentity: (identity) => set({ identity }),
  setAudioLevel: (audioLevel) => set({ audioLevel }),
  setError: (error) => set({ error }),

  addTranscript: (message) =>
    set((state) => ({
      transcripts: [...state.transcripts, message],
    })),

  clearTranscripts: () => set({ transcripts: [] }),

  reset: () => set(initialState),
}));