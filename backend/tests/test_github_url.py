"""Unit tests for GitHub URL validation + parsing (Phase 1)."""
import pytest
from pydantic import ValidationError

from app.modules.projects.validators.schemas import (
    GitHubImportRequest,
    parse_github_url,
)


@pytest.mark.parametrize(
    "url,owner,repo",
    [
        ("https://github.com/torvalds/linux", "torvalds", "linux"),
        ("https://github.com/user/project.git", "user", "project"),
        ("http://github.com/a/b/", "a", "b"),
        ("github.com/octocat/Hello-World", "octocat", "Hello-World"),
    ],
)
def test_valid_github_urls(url, owner, repo):
    req = GitHubImportRequest(repo_url=url)
    assert parse_github_url(req.repo_url) == (owner, repo)


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/user/project",
        "https://github.com/onlyowner",
        "not-a-url",
        "https://evil.com/github.com/a/b",
        "",
    ],
)
def test_invalid_github_urls_rejected(url):
    with pytest.raises(ValidationError):
        GitHubImportRequest(repo_url=url)
