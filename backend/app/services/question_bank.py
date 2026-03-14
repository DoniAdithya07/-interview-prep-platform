import random


QUESTION_BANK = {
    "technical": {
        "frontend": [
            "Explain the browser event loop and how microtasks differ from macrotasks.",
            "Walk through how React reconciles updates and how you would debug a re-render loop.",
            "What causes layout thrashing and how do you detect and fix it?",
        ],
        "backend": [
            "How would you design idempotent HTTP APIs and enforce that at the data layer?",
            "Explain connection pooling and how you'd tune it for a high-traffic FastAPI service.",
            "Describe how you'd roll out feature flags safely across services.",
        ],
        "general": [
            "Explain CAP theorem in practical terms and give a system that prioritizes each axis.",
            "How do you measure and improve P99 latency for an API?",
        ],
    },
    "coding": {
        "algorithms": [
            "Given an array of integers, return the length of the longest increasing subsequence.",
            "Implement an LRU cache with O(1) get and put.",
            "Find the minimum window substring containing all characters of another string.",
        ],
        "data-structures": [
            "Design a stack with O(1) getMin and getMax.",
            "Implement a Trie that supports prefix search and deletion.",
        ],
        "general": [
            "Solve the Two Sum variant where you return all unique pairs sorted by index.",
        ],
    },
    "behavioral": {
        "communication": [
            "Tell me about a time you had to deliver bad news to stakeholders. What was the outcome?",
            "Describe a situation where you had to align multiple teams with conflicting priorities.",
        ],
        "leadership": [
            "Give an example of when you took ownership of a failing project. What did you change?",
            "Tell me about a conflict you resolved within your team.",
        ],
        "general": [
            "Describe your most impactful project and how you measured success.",
        ],
    },
    "hr": {
        "general": [
            "Why are you looking to move right now, and what matters most in your next role?",
            "Describe your ideal team culture and how you contribute to it.",
            "Tell me about compensation expectations and how you think about tradeoffs.",
        ],
    },
    "system-design": {
        "general": [
            "Design a notifications platform supporting email, push, and in-app with retries and rate limiting.",
            "Design a URL shortener with custom domains and analytics.",
            "Design a real-time collaborative document editor.",
        ],
        "scalability": [
            "Design a rate limiter for a multi-tenant API with burst control and fairness.",
            "Design a feed system that supports ranking, fan-out, and deduplication.",
        ],
    },
    "ai-mock": {
        "general": [
            "Run a full mock: start with 'Tell me about a challenging project' then follow with a probing technical question.",
            "Kick off a mixed interview: start with a system design scoping question, then ask for a coding follow-up.",
        ],
    },
}


def random_question(mode: str, topic: str | None = None, exclude: str | None = None) -> str | None:
    mode_key = mode.strip().lower()
    topic_key = (topic or "general").strip().lower()
    bank = QUESTION_BANK.get(mode_key)
    if not bank:
        return None

    candidates = list(bank.get(topic_key, []))
    if exclude in candidates and len(candidates) > 1:
        candidates = [q for q in candidates if q != exclude]
    if candidates:
        return random.choice(candidates)

    general = list(bank.get("general") or [])
    if exclude in general and len(general) > 1:
        general = [q for q in general if q != exclude]
    if general:
        return random.choice(general)

    flat = [q for questions in bank.values() for q in questions if exclude is None or q != exclude or len(questions) == 1]
    return random.choice(flat) if flat else None
