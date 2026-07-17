"""Language detection rules — extension, special-filename, and shebang maps.

Data only; the detector applies these. Add a language by adding a row here, no
detector changes needed (open/closed principle).
"""

# File extension (lowercased, including the dot) -> language label.
EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".pyw": "Python",
    ".pyi": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".vue": "JavaScript",
    ".svelte": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".hh": "C++",
    ".hxx": "C++",
    ".dart": "Dart",
    ".scala": "Scala",
    ".m": "Objective-C",
    ".mm": "Objective-C",
    ".lua": "Lua",
    ".pl": "Perl",
    ".pm": "Perl",
    ".r": "R",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".less": "CSS",
}

# Exact filename (no extension) -> language label.
FILENAME_LANGUAGE: dict[str, str] = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "CMakeLists.txt": "CMake",
}

# Shebang interpreter basename -> language (for extensionless executables).
SHEBANG_LANGUAGE: dict[str, str] = {
    "python": "Python",
    "python3": "Python",
    "node": "JavaScript",
    "bash": "Shell",
    "sh": "Shell",
    "zsh": "Shell",
    "ruby": "Ruby",
    "perl": "Perl",
    "php": "PHP",
}

# Languages excluded from "primary language" selection (markup/styling/config):
# they often dominate file counts without representing the project's core logic.
NON_PRIMARY_LANGUAGES: frozenset[str] = frozenset(
    {"HTML", "CSS", "SQL", "Shell", "PowerShell", "Dockerfile", "Makefile", "CMake"}
)
