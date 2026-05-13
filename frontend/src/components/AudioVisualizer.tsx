import React, { useRef, useEffect } from "react";
import { useAgentStore } from "../store/agentStore";

interface Props {
  barCount?: number;
}

export const AudioVisualizer: React.FC<Props> = ({ barCount = 32 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const audioLevel = useAgentStore((s) => s.audioLevel);
  const speaking = useAgentStore((s) => s.speaking);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const draw = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      const barWidth = width / barCount;
      const gap = 2;

      for (let i = 0; i < barCount; i++) {
        const x = i * barWidth + gap / 2;
        const barH = audioLevel * height * (0.3 + Math.random() * 0.7);

        ctx.fillStyle = speaking
          ? `hsl(${160 + i * 3}, 80%, 60%)`
          : `hsl(${220 + i * 2}, 40%, 50%)`;
        ctx.fillRect(x, height - barH, barWidth - gap, barH);
      }

      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [audioLevel, speaking, barCount]);

  return (
    <canvas
      ref={canvasRef}
      width={320}
      height={80}
      className="rounded-lg bg-gray-900/50"
    />
  );
};