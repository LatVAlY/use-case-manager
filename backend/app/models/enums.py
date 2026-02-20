import enum


class UserRole(str, enum.Enum):
    reader = "reader"
    maintainer = "maintainer"
    admin = "admin"


class UseCaseStatus(str, enum.Enum):
    new = "new"
    under_review = "under_review"
    approved = "approved"
    in_progress = "in_progress"
    completed = "completed"
    archived = "archived"


class RelationType(str, enum.Enum):
    depends_on = "depends_on"
    complements = "complements"
    conflicts_with = "conflicts_with"
    duplicates = "duplicates"


class TranscriptStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    completed = "completed"
    failed = "failed"
