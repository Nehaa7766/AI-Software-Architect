"""Framework + package-manager detection rules driven by manifest files.

Each :class:`ManifestRule` maps a manifest filename to the package manager it
implies and a set of dependency-token -> framework signatures. Adding support
for a new framework is a data change here, not a code change in the detector.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ManifestRule:
    # Manifest filename to look for (matched case-insensitively, basename only).
    filename: str
    # Package manager this manifest implies (empty string = none).
    package_manager: str = ""
    # Framework always implied by the manifest's mere presence (e.g. Node.js).
    base_framework: str = ""
    # token (substring, lowercased) -> framework name.
    signatures: dict[str, str] = field(default_factory=dict)
    # If True the file is parsed as JSON and only dependency *keys* are scanned;
    # otherwise the raw text is substring-searched (good enough for xml/toml/yaml).
    json_deps: bool = False


MANIFEST_RULES: tuple[ManifestRule, ...] = (
    ManifestRule(
        filename="package.json",
        package_manager="npm",
        base_framework="Node.js",
        json_deps=True,
        signatures={
            "next": "Next.js",
            "react": "React",
            "@angular/core": "Angular",
            "vue": "Vue",
            "nuxt": "Nuxt",
            "svelte": "Svelte",
            "@nestjs/core": "NestJS",
            "express": "Express",
            "electron": "Electron",
            "gatsby": "Gatsby",
            "@remix-run/react": "Remix",
        },
    ),
    ManifestRule(
        filename="requirements.txt",
        package_manager="pip",
        signatures={"fastapi": "FastAPI", "django": "Django", "flask": "Flask"},
    ),
    ManifestRule(
        filename="pyproject.toml",
        package_manager="pip",
        signatures={"fastapi": "FastAPI", "django": "Django", "flask": "Flask"},
    ),
    ManifestRule(
        filename="Pipfile",
        package_manager="pipenv",
        signatures={"fastapi": "FastAPI", "django": "Django", "flask": "Flask"},
    ),
    ManifestRule(
        filename="setup.py",
        package_manager="pip",
        signatures={"fastapi": "FastAPI", "django": "Django", "flask": "Flask"},
    ),
    ManifestRule(
        filename="pom.xml",
        package_manager="Maven",
        signatures={"spring-boot": "Spring Boot"},
    ),
    ManifestRule(
        filename="build.gradle",
        package_manager="Gradle",
        signatures={"spring-boot": "Spring Boot"},
    ),
    ManifestRule(
        filename="build.gradle.kts",
        package_manager="Gradle",
        signatures={"spring-boot": "Spring Boot"},
    ),
    ManifestRule(filename="go.mod", package_manager="Go Modules"),
    ManifestRule(filename="Cargo.toml", package_manager="Cargo"),
    ManifestRule(
        filename="composer.json",
        package_manager="Composer",
        json_deps=True,
        signatures={"laravel/framework": "Laravel", "symfony/": "Symfony"},
    ),
    ManifestRule(
        filename="Gemfile",
        package_manager="Bundler",
        signatures={"rails": "Ruby on Rails"},
    ),
    ManifestRule(
        filename="pubspec.yaml",
        package_manager="Pub",
        signatures={"flutter": "Flutter"},
    ),
)

# Glob-matched manifests (handled separately because the name varies).
# suffix (lowercased) -> (package_manager, {token: framework})
SUFFIX_MANIFEST_RULES: dict[str, tuple[str, dict[str, str]]] = {
    ".csproj": ("NuGet", {"microsoft.aspnetcore": "ASP.NET", "microsoft.net.sdk.web": "ASP.NET"}),
}

# Lockfile presence -> the package manager it pins (overrides/augments above).
LOCKFILE_PACKAGE_MANAGERS: dict[str, str] = {
    "yarn.lock": "Yarn",
    "pnpm-lock.yaml": "pnpm",
    "package-lock.json": "npm",
    "poetry.lock": "Poetry",
    "Pipfile.lock": "pipenv",
    "Gemfile.lock": "Bundler",
    "Cargo.lock": "Cargo",
    "composer.lock": "Composer",
}
