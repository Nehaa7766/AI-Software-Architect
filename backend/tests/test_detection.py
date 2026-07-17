"""Unit tests for Phase 2 language + framework detection."""
import json
from pathlib import Path

from app.modules.projects.services.detection import DetectionService
from app.modules.projects.services.detection.language_detector import LanguageDetector
from app.modules.projects.utils.ignore_rules import walk_files


def _write(root: Path, rel: str, content: str = "x") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_language_classification_by_extension():
    det = LanguageDetector()
    assert det.classify(Path("a/b/main.py")) == "Python"
    assert det.classify(Path("x.tsx")) == "TypeScript"
    assert det.classify(Path("Dockerfile")) == "Dockerfile"
    assert det.classify(Path("notes.unknownext")) is None


def test_walk_files_prunes_ignored_dirs(tmp_path: Path):
    _write(tmp_path, "src/app.py")
    _write(tmp_path, "node_modules/dep/index.js")
    _write(tmp_path, ".git/config")
    names = {p.name for p in walk_files(tmp_path)}
    assert "app.py" in names
    assert "index.js" not in names  # node_modules pruned
    assert "config" not in names  # .git pruned


def test_detect_python_fastapi_project(tmp_path: Path):
    _write(tmp_path, "app/main.py", "print('hi')\n")
    _write(tmp_path, "app/routes.py", "x = 1\n")
    _write(tmp_path, "requirements.txt", "fastapi>=0.111\nuvicorn\n")
    # Noise that must be ignored:
    _write(tmp_path, ".venv/lib/site.py", "ignored")

    stack = DetectionService().detect(tmp_path)
    assert stack["primary_language"] == "Python"
    assert "FastAPI" in stack["frameworks"]
    assert "pip" in stack["package_managers"]
    langs = {l["language"]: l["files"] for l in stack["languages"]}
    assert langs["Python"] == 2  # .venv pruned, only the 2 app files


def test_detect_node_react_next_project(tmp_path: Path):
    pkg = {
        "dependencies": {"react": "^18", "next": "^14"},
        "devDependencies": {"typescript": "^5"},
    }
    _write(tmp_path, "package.json", json.dumps(pkg))
    _write(tmp_path, "pnpm-lock.yaml", "lockfileVersion: 6.0")
    _write(tmp_path, "src/page.tsx", "export default null")
    _write(tmp_path, "src/util.ts", "export const x = 1")

    stack = DetectionService().detect(tmp_path)
    assert stack["primary_language"] == "TypeScript"
    assert "React" in stack["frameworks"]
    assert "Next.js" in stack["frameworks"]
    assert "Node.js" in stack["frameworks"]
    assert "pnpm" in stack["package_managers"]


def test_percentages_sum_about_100(tmp_path: Path):
    _write(tmp_path, "a.py", "x" * 100)
    _write(tmp_path, "b.js", "y" * 100)
    stack = DetectionService().detect(tmp_path)
    total = sum(l["percentage"] for l in stack["languages"])
    assert 99.0 <= total <= 101.0


def test_empty_project_detects_nothing(tmp_path: Path):
    _write(tmp_path, "README.md", "# nothing to see")
    stack = DetectionService().detect(tmp_path)
    assert stack["primary_language"] is None
    assert stack["languages"] == []
    assert stack["frameworks"] == []
