"""Pydantic request schemas for the projects module."""
import re

from pydantic import BaseModel, Field, field_validator

# Accepts https://github.com/<owner>/<repo>(.git)(/...) and bare owner/repo paths.
_GITHUB_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})?)/"
    r"(?P<repo>[A-Za-z0-9_.-]{1,100}?)(?:\.git)?/?$",
    re.IGNORECASE,
)


class GitHubImportRequest(BaseModel):
    """Import a public GitHub repository by URL."""

    repo_url: str = Field(min_length=1, max_length=1024)
    # Optional explicit branch; defaults to the repo's default branch.
    branch: str | None = Field(default=None, max_length=255)

    @field_validator("repo_url")
    @classmethod
    def _validate_github_url(cls, v: str) -> str:
        if not _GITHUB_RE.match(v.strip()):
            raise ValueError("Must be a valid public GitHub repository URL.")
        return v.strip()


def parse_github_url(repo_url: str) -> tuple[str, str]:
    """Extract ``(owner, repo)`` from a validated GitHub URL.

    Returns the pair; raises ValueError if it does not match (defensive — the
    schema validator should have caught it already).
    """
    match = _GITHUB_RE.match(repo_url.strip())
    if not match:
        raise ValueError("Invalid GitHub repository URL.")
    return match.group("owner"), match.group("repo")
