"""
PeerSpace Server Entrypoint
Runs the modular FastAPI application with uvicorn.
"""

import sys
import logging
import uvicorn
from backend.app import app
from backend.config import HOST, PORT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("peerspace")

if __name__ == "__main__":
    logger.info("Starting PeerSpace server on http://%s:%d", HOST, PORT)
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=False)
