COMPANY_PROFILES = {
    "google": "Focus on first-principles reasoning, scalable design, and clear tradeoff discussion.",
    "amazon": "Probe ownership, leadership principles, customer impact, and pragmatic decision making.",
    "meta": "Emphasize product thinking, execution speed, and systems that scale to large user bases.",
    "microsoft": "Look for collaboration, reliability, engineering discipline, and growth mindset.",
}


def get_company_profile(company: str | None) -> str:
    if not company:
        return "Use a realistic but generic interview style."
    return COMPANY_PROFILES.get(company.strip().lower(), f"Use a {company} interview style.")
