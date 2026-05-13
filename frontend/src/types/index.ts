export interface TranscriptMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

export interface AgentState {
  connected: boolean;
  connecting: boolean;
  muted: boolean;
  speaking: boolean;
  roomName: string;
  identity: string;
  transcripts: TranscriptMessage[];
  audioLevel: number;
  error: string | null;
}

export interface TokenResponse {
  token: string;
  room_name: string;
  identity: string;
  server_url: string;
}

export interface DocumentUploadResponse {
  doc_id: string;
  filename: string;
  status: string;
  chunks: number;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  services: Record<string, unknown>;
}