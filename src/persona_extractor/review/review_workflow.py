from __future__ import annotations


def prepare_review_queue(experiences: list[dict]) -> list[dict]:
    return [{"review_status": "pending", "experience": experience} for experience in experiences]
