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

# Ensure Psycopg 3 compatible SelectorEventLoop on Windows
if sys.platform == "win32":
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

if __name__ == "__main__":
    logger.info("Starting PeerSpace server on http://%s:%d", HOST, PORT)
    loop_opt = "asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto"
    uvicorn.run(
        "backend.app:app", 
        host=HOST, 
        port=PORT, 
        reload=False,
        loop=loop_opt,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
