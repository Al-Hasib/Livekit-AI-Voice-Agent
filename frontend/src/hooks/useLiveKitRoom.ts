import { useCallback, useEffect, useRef } from "react";
import {
  Room,
  RoomEvent,
  Track,
  LocalParticipant,
  RemoteParticipant,
  RemoteTrackPublication,
  RemoteTrack,
  ConnectionState,
} from "livekit-client";
import { api } from "../services/api";
import { useAgentStore } from "../store/agentStore";

export function useLiveKitRoom() {
  const roomRef = useRef<Room | null>(null);
  const {
    setConnected,
    setConnecting,
    setMuted,
    setSpeaking,
    addTranscript,
    setError,
    setRoomName,
    setIdentity,
    reset,
  } = useAgentStore();

  const connect = useCallback(async (identity: string, roomName: string) => {
    try {
      setConnecting(true);
      setError(null);
      setRoomName(roomName);
      setIdentity(identity);

      // Get token from backend
      const tokenData = await api.createToken(identity, roomName);

      // Create and connect to room
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          noiseSuppression: true,
          echoCancellation: true,
          autoGainControl: true,
        },
      });

      // Set up event listeners
      room.on(RoomEvent.Connected, () => {
        setConnected(true);
        setConnecting(false);
        console.log("Connected to room:", room.name);
      });

      room.on(RoomEvent.Disconnected, () => {
        setConnected(false);
        setConnecting(false);
      });

      room.on(RoomEvent.Reconnecting, () => {
        setConnecting(true);
      });

      room.on(RoomEvent.Reconnected, () => {
        setConnecting(false);
        setConnected(true);
      });

      room.on(
        RoomEvent.TrackSubscribed,
        (
          _track: RemoteTrack,
          publication: RemoteTrackPublication,
          _participant: RemoteParticipant
        ) => {
          if (publication.kind === Track.Kind.Audio) {
            console.log("Agent audio track subscribed");
          }
        }
      );

      room.on(RoomEvent.LocalTrackPublished, () => {
        console.log("Local track published");
      });

      room.on(RoomEvent.ActiveSpeakersChanged, (speakers: (LocalParticipant | RemoteParticipant)[]) => {
        const isAgentSpeaking = speakers.some((s) => !s.isLocal);
        const isUserSpeaking = speakers.some((s) => s.isLocal);
        setSpeaking(isAgentSpeaking || isUserSpeaking);
      });

      room.on(RoomEvent.DataReceived, (payload: Uint8Array) => {
        try {
          const data = JSON.parse(new TextDecoder().decode(payload));
          if (data.type === "transcript") {
            addTranscript({
              id: crypto.randomUUID(),
              role: data.role,
              content: data.content,
              timestamp: Date.now(),
            });
          }
        } catch {
          // Ignore non-JSON data
        }
      });

      // Connect
      await room.connect(tokenData.server_url, tokenData.token);
      roomRef.current = room;

      // Enable microphone
      await room.localParticipant.setMicrophoneEnabled(true);
      setMuted(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Connection failed";
      setError(message);
      setConnecting(false);
      setConnected(false);
    }
  }, [setConnected, setConnecting, setMuted, setSpeaking, addTranscript, setError, setRoomName, setIdentity]);

  const disconnect = useCallback(async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    reset();
  }, [reset]);

  const toggleMute = useCallback(async () => {
    if (!roomRef.current) return;

    const enabled = roomRef.current.localParticipant.isMicrophoneEnabled;
    await roomRef.current.localParticipant.setMicrophoneEnabled(!enabled);
    setMuted(enabled);
  }, [setMuted]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
        roomRef.current = null;
      }
    };
  }, []);

  return {
    connect,
    disconnect,
    toggleMute,
    room: roomRef.current,
  };
}