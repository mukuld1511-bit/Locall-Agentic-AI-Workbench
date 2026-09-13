from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageSpec:
    key: str
    label: str
    extension: str
    command: tuple[str, ...]
    executable: str


LANGUAGES = (
    LanguageSpec(
        "python",
        "Python",
        ".py",
        ("python3", "{file}"),
        "python3",
    ),
    LanguageSpec(
        "javascript",
        "JavaScript",
        ".js",
        ("node", "{file}"),
        "node",
    ),
    LanguageSpec(
        "typescript",
        "TypeScript",
        ".ts",
        ("npx", "tsx", "{file}"),
        "npx",
    ),
    LanguageSpec(
        "c",
        "C",
        ".c",
        ("bash", "-lc", "gcc {file} -o {bin} && {bin}"),
        "gcc",
    ),
    LanguageSpec(
        "cpp",
        "C++",
        ".cpp",
        ("bash", "-lc", "g++ {file} -o {bin} && {bin}"),
        "g++",
    ),
    LanguageSpec(
        "java",
        "Java",
        ".java",
        ("bash", "-lc", "javac {file} && java -cp {dir} {class}"),
        "javac",
    ),
    LanguageSpec(
        "go",
        "Go",
        ".go",
        ("go", "run", "{file}"),
        "go",
    ),
    LanguageSpec(
        "rust",
        "Rust",
        ".rs",
        ("bash", "-lc", "rustc {file} -o {bin} && {bin}"),
        "rustc",
    ),
    LanguageSpec(
        "bash",
        "Bash",
        ".sh",
        ("bash", "{file}"),
        "bash",
    ),
    LanguageSpec(
        "php",
        "PHP",
        ".php",
        ("php", "{file}"),
        "php",
    ),
    LanguageSpec(
        "ruby",
        "Ruby",
        ".rb",
        ("ruby", "{file}"),
        "ruby",
    ),
    LanguageSpec(
        "kotlin",
        "Kotlin",
        ".kt",
        ("bash", "-lc", "kotlinc {file} -include-runtime -d {bin}.jar && java -jar {bin}.jar"),
        "kotlinc",
    ),
)


def available_languages():
    result = []

    for spec in LANGUAGES:
        installed = shutil.which(
            spec.executable
        )

        result.append({
            "key": spec.key,
            "label": spec.label,
            "extension": spec.extension,
            "available": bool(installed),
            "executable": installed or "",
        })

    return result
