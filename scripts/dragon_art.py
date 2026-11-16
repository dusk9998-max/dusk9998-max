import base64
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=8)
def embedded_art(name: str) -> str:
    content = (Path(__file__).resolve().parents[1] / "assets" / "paper-dragon" / name).read_bytes()
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif content.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    else:
        raise ValueError("Invalid dragon artwork asset.")
    return "data:" + mime + ";base64," + base64.b64encode(content).decode("ascii")
