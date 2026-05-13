#!/usr/bin/env python3
"""LiveKit Agent Worker entry point.

This runs as a separate process that connects to the LiveKit server
and handles voice agent jobs.
"""

import asyncio

import structlog
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli

from app.config import get_settings
from app.utils.logger import setup_logger
from app.agent.pipeline import create_voice_pipeline, get_rag_service

logger = structlog.get_logger(__name__)


async def entrypoint(ctx: JobContext) -> None:
    """Main entry point for each agent job (one per room)."""

    settings = get_settings()

    logger.info(
        "agent_job_started",
        room=ctx.room.name if ctx.room else "unknown",
        job_id=ctx.job.id if ctx.job else "unknown",
    )

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    logger.info("agent_connected_to_room", room=ctx.room.name)

    # Pre-warm RAG service (load models, ensure collection)
    rag_service = get_rag_service()
    try:
        await rag_service.vector_store.ensure_collection()
        logger.info("rag_service_ready")
    except Exception as e:
        logger.warning("rag_warmup_failed", error=str(e))

    # Create the voice pipeline
    agent = create_voice_pipeline()

    # Start the agent in the room
    agent.start(ctx.room)

    # Greet the user
    await agent.say("Hey, how can I help you today?")

    logger.info("agent_started", room=ctx.room.name)


def main() -> None:
    """Start the agent worker."""
    settings = get_settings()
    setup_logger(settings.log_level)

    logger.info(
        "starting_agent_worker",
        livekit_url=settings.livekit_url,
        environment=settings.environment,
    )

    # Run the LiveKit agent worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Process jobs as they arrive
            preemptive_flush=True,
            # Worker metadata for monitoring
            job_executor_type="threaded",
        ),
    )


if __name__ == "__main__":
    main()