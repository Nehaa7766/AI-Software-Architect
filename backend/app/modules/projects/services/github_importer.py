"""GitHub import — download a public repo's zipball into the temp dir.

Uses the codeload zip endpoint (no ``git`` binary required) and reuses the same
safe extractor as ZIP uploads. Private repos are out of scope for Phase 1.
Blocking ``requests`` calls run in a worker thread so the event loop is free.
"""
import asyncio

import requests

from app.core.config import settings
from app.models.project import ImportSource
from app.modules.projects.services.staging import StagedArchive
from app.modules.projects.services.validator import ProjectValidator
from app.modules.projects.services.workspace_manager import WorkspaceManager
from app.modules.projects.utils.exceptions import (
    FileTooLarge,
    RepositoryUnavailable,
)
from app.modules.projects.utils.zip_safety import sanitize_project_name
from app.modules.projects.validators.schemas import parse_github_url

_CHUNK = 1024 * 1024


class GitHubImporter:
    def __init__(
        self, *, validator: ProjectValidator, workspace: WorkspaceManager
    ) -> None:
        self.validator = validator
        self.workspace = workspace

    async def stage(self, *, repo_url: str, branch: str | None) -> StagedArchive:
        owner, repo = parse_github_url(repo_url)
        return await asyncio.to_thread(self._stage_sync, owner, repo, repo_url, branch)

    # ---- blocking section (runs in a thread) ----
    def _stage_sync(
        self, owner: str, repo: str, repo_url: str, branch: str | None
    ) -> StagedArchive:
        resolved_branch = branch or self._default_branch(owner, repo)
        tmp_path = self.workspace.new_tmp_file(".zip")
        url = (
            f"{settings.GITHUB_CODELOAD_BASE}/{owner}/{repo}"
            f"/zip/refs/heads/{resolved_branch}"
        )
        try:
            self._download(url, tmp_path)
            self.validator.validate_zip_file(tmp_path)
        except Exception:
            self.workspace.remove_file(tmp_path)
            raise

        return StagedArchive(
            tmp_path=tmp_path,
            project_name=sanitize_project_name(repo),
            source_type=ImportSource.GITHUB,
            source_location=repo_url,
        )

    def _default_branch(self, owner: str, repo: str) -> str:
        try:
            resp = requests.get(
                f"{settings.GITHUB_API_BASE}/repos/{owner}/{repo}",
                timeout=settings.GITHUB_DOWNLOAD_TIMEOUT_SECONDS,
                headers={"Accept": "application/vnd.github+json"},
            )
        except requests.RequestException as exc:
            raise RepositoryUnavailable("Could not reach GitHub.") from exc
        if resp.status_code == 404:
            raise RepositoryUnavailable("Repository not found or is private.")
        if resp.status_code != 200:
            raise RepositoryUnavailable(
                f"GitHub returned status {resp.status_code}."
            )
        return resp.json().get("default_branch") or "main"

    def _download(self, url: str, dest) -> None:
        try:
            with requests.get(
                url,
                stream=True,
                timeout=settings.GITHUB_DOWNLOAD_TIMEOUT_SECONDS,
            ) as resp:
                if resp.status_code == 404:
                    raise RepositoryUnavailable(
                        "Repository or branch not found."
                    )
                if resp.status_code != 200:
                    raise RepositoryUnavailable(
                        f"Download failed with status {resp.status_code}."
                    )
                written = 0
                with open(dest, "wb") as out:
                    for chunk in resp.iter_content(chunk_size=_CHUNK):
                        if not chunk:
                            continue
                        written += len(chunk)
                        if written > settings.MAX_PROJECT_BYTES:
                            raise FileTooLarge(
                                "Repository archive exceeds the size limit."
                            )
                        out.write(chunk)
        except requests.RequestException as exc:
            raise RepositoryUnavailable(f"Download failed: {exc}") from exc
