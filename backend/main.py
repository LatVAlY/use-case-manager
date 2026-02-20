"""CLI entry point - run with: python main.py or uvicorn main:app"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        loop="asyncio",
    )
