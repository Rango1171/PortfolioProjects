"""
Detects whether a job posting sponsors foreign workers.
Returns "Yes", "No", or "Unknown" based on keyword scanning of the JD text.
"""

YES_PATTERNS = [
    "visa sponsor",
    "we sponsor",
    "sponsorship provided",
    "sponsorship available",
    "work permit sponsor",
    "relocation package",
    "relocation support",
    "relocation assistance",
    "visa support",
    "immigration support",
    "we will sponsor",
    "can sponsor",
    "able to sponsor",
    "sponsoring the visa",
    "work authorization sponsor",
    "h-1b sponsor",
    "tier 2 sponsor",
    "skilled worker visa",
    "we provide visa",
    "visa assistance",
    "open to sponsorship",
    "sponsorship considered",
    "visa relocation",
]

NO_PATTERNS = [
    "no sponsorship",
    "no visa sponsor",
    "not able to sponsor",
    "unable to sponsor",
    "cannot sponsor",
    "won't sponsor",
    "will not sponsor",
    "does not sponsor",
    "sponsorship is not",
    "no work permit",
    "must have right to work",
    "must be eligible to work",
    "must already have the right to work",
    "right to work in",
    "must hold a valid work permit",
    "eu citizens only",
    "eea citizens only",
    "nationals only",
    "local candidates only",
    "local applicants only",
    "candidates must be based in",
    "no relocation",
    "authorization to work",
    "legally authorized to work",
    "without sponsorship",
]


def detect_sponsorship(text: str) -> str:
    """
    Scan job description text and return sponsorship status.
    "Yes"     → explicitly offers visa sponsorship / relocation
    "No"      → explicitly states no sponsorship or requires existing right to work
    "Unknown" → no clear signal found
    """
    if not text:
        return "Unknown"

    lower = text.lower()

    for pattern in YES_PATTERNS:
        if pattern in lower:
            return "Yes"

    for pattern in NO_PATTERNS:
        if pattern in lower:
            return "No"

    return "Unknown"
