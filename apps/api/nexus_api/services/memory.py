import hashlib
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_api.models import Memory


def embed_text(text: str, dimensions: int = 64) -> list[float]:
    buckets = [0.0] * dimensions
    tokens = [token.lower() for token in text.split() if token.strip()]
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        index = digest[0] % dimensions
        sign = 1 if digest[1] % 2 == 0 else -1
        buckets[index] += sign * (1 + len(token) / 12)
    norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
    return [round(value / norm, 6) for value in buckets]


def remember(
    db: Session,
    *,
    organization_id: str,
    agent_id: str | None,
    memory_type: str,
    content: str,
    importance: float,
    meta: dict | None = None,
) -> Memory:
    memory = Memory(
        organization_id=organization_id,
        agent_id=agent_id,
        memory_type=memory_type,
        content=content,
        importance=importance,
        embedding=embed_text(content),
        meta=meta or {},
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def recall(db: Session, *, organization_id: str, query: str, limit: int = 8) -> list[Memory]:
    query_vector = embed_text(query)
    memories = list(
        db.scalars(
            select(Memory)
            .where(Memory.organization_id == organization_id)
            .order_by(Memory.importance.desc(), Memory.created_at.desc())
            .limit(100)
        )
    )
    scored = []
    for memory in memories:
        score = sum(a * b for a, b in zip(query_vector, memory.embedding, strict=False))
        scored.append((score + memory.importance * 0.1, memory))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [memory for _, memory in scored[:limit]]

