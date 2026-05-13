import { useEffect, useRef } from "react";
import { useAgentStore } from "../store/agentStore";

export function useAudioAnalyzer() {
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const { setAudioLevel } = useAgentStore();

  useEffect(() => {
    const analyze = () => {
      if (analyserRef.current) {
        const data = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(data);

        const average = data.reduce((sum, val) => sum + val, 0) / data.length;
        const normalized = Math.min(average / 128, 1);
        setAudioLevel(normalized);
      }
      animFrameRef.current = requestAnimationFrame(analyze);
    };

    analyze();

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [setAudioLevel]);

  return { analyserRef };
}