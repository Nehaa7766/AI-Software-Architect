"""View layer (presenters) for the projects module.

The MVC "V": maps domain models (ORM ``Project``) into the response DTOs the
client receives. Centralizing the mapping here keeps controllers free of any
serialization detail — a controller asks the view for a ready-to-return body —
and keeps the DTOs in ``dto/`` as pure schemas with no mapping logic.
"""
from app.models.project import Project
from app.modules.projects.dto.responses import (
    MessageResponse,
    ProjectListResponse,
    ProjectResponse,
)


class ProjectView:
    """Presents domain models as response DTOs (model -> view)."""

    @staticmethod
    def detail(project: Project) -> ProjectResponse:
        # from_attributes=True on the DTO maps ORM fields (incl. the JSON stack).
        return ProjectResponse.model_validate(project)

    @staticmethod
    def collection(projects: list[Project], total: int) -> ProjectListResponse:
        return ProjectListResponse(
            projects=[ProjectView.detail(p) for p in projects],
            total=total,
        )

    @staticmethod
    def message(message: str) -> MessageResponse:
        return MessageResponse(message=message)
