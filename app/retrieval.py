import glob
import logging

import frontmatter
import httpx
import numpy as np

from .config import settings

log = logging.getLogger(__name__)

EMBED_DIM = 768
SOPS: list[dict] = []


def _embed(text: str) -> np.ndarray:
    response = httpx.post(
        f"{settings.ollama_base_url}/api/embeddings",
        json={"model": settings.ollama_embed_model, "prompt": text},
        timeout=30.0,
    )
    response.raise_for_status()
    vec = np.array(response.json()["embedding"], dtype=np.float32)
    if vec.shape != (EMBED_DIM,):
        raise ValueError(f"Expected {EMBED_DIM}-dim vector, got {vec.shape}")
    norm = np.linalg.norm(vec)
    return vec / (norm + 1e-9)


def load_sops(sop_dir: str = "sops/*.md") -> None:
    SOPS.clear()
    paths = glob.glob(sop_dir)
    if not paths:
        raise RuntimeError(f"No SOP files found matching '{sop_dir}'")
    for path in paths:
        post = frontmatter.load(path)
        embedding = _embed(post.metadata["title"] + "\n" + post.content)
        SOPS.append(
            {
                "id": post.metadata["id"],
                "title": post.metadata["title"],
                "text": post.content,
                "embedding": embedding,
            }
        )
    log.info("loaded %d SOPs, embedding dim=%d", len(SOPS), EMBED_DIM)


def top_k(query: str, k: int = 3) -> list[dict]:
    if not SOPS:
        raise RuntimeError("SOPs not loaded — call load_sops() first")
    q = _embed(query)
    scored = [(float(np.dot(q, sop["embedding"])), sop) for sop in SOPS]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [sop for _, sop in scored[:k]]
