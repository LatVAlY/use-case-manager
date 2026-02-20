import json
from typing import AsyncGenerator
from redis import Redis
from app.config import settings


async def subscribe_to_transcript_progress(transcript_id: str) -> AsyncGenerator[str, None]:
    """
    Subscribe to transcript processing progress via Server-Sent Events.
    Yields SSE-formatted messages until completion or failure.
    """
    redis_client = Redis.from_url(settings.REDIS_URL)
    pubsub = redis_client.pubsub()
    channel = f"transcript:{transcript_id}"
    
    try:
        pubsub.subscribe(channel)
        
        for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                yield f"data: {json.dumps(data)}\n\n"
                
                # Close connection on completion or failure
                if data.get("event") in ("completed", "failed"):
                    break
    finally:
        pubsub.unsubscribe(channel)
        pubsub.close()
