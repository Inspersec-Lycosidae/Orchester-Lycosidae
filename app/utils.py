from fastapi import HTTPException
import re
def sanitize_container_name(name: str) -> str:
    """
    Sanitize a string to be safe as a Docker container name.
    Allows only letters, numbers, hyphens, and underscores.
    Replaces all other characters with underscore.
    """
    if not name:
        raise HTTPException(status_code=400, detail="Container name cannot be empty")
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def validate_time_alive(time_alive: int, max_seconds: int = 15552000) -> int: #max 6 months uptime
    """
    Validate time_alive is a positive integer <= max_seconds (default 6 months).
    """
    if not isinstance(time_alive, int) or time_alive <= 0 or time_alive > max_seconds:
        raise HTTPException(status_code=400, detail=f"time_alive must be between 1 and {max_seconds} seconds")
    return time_alive

import socket

def find_free_port(start: int = 50000, end: int = 60000) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if s.connect_ex(("0.0.0.0", port)) != 0:  # port is free
                return port
    raise RuntimeError("No free ports available in range 50000-60000")