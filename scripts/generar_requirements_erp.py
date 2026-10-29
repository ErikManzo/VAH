#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Genera un requirements.txt reproducible para el ERP VAH.

Criterio:
- Si una distribucion ya esta instalada en el entorno activo, la fija con `==`.
- Si no esta instalada, usa un rango compatible definido como fallback.

Uso:
    python scripts/generar_requirements_erp.py
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from pathlib import Path


@dataclass(frozen=True)
class Dependency:
    name: str
    fallback: str
    section: str


DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency("PyQt6", "PyQt6>=6.5,<7", "Runtime"),
    Dependency("pyodbc", "pyodbc>=5.0,<6", "Runtime"),
    Dependency("pandas", "pandas>=2.2,<3", "Runtime"),
    Dependency("numpy", "numpy>=1.26,<2", "Runtime"),
    Dependency("openpyxl", "openpyxl>=3.1,<4", "Runtime"),
    Dependency("reportlab", "reportlab>=4.0,<5", "Runtime"),
    Dependency("pdfplumber", "pdfplumber>=0.11,<1", "Runtime"),
    Dependency("Pillow", "Pillow>=10,<13", "Runtime"),
    Dependency("pywin32", "pywin32>=306", "Runtime"),
    Dependency("pyspellchecker", "pyspellchecker>=0.8,<1", "Optional"),
    Dependency("language_tool_python", "language_tool_python>=2.9,<3", "Optional"),
    Dependency("pyinstaller", "pyinstaller>=6.0,<7", "Build"),
    Dependency("pyinstaller-hooks-contrib", "pyinstaller-hooks-contrib>=2025.0", "Build"),
)


def resolve_requirement(dep: Dependency) -> str:
    try:
        version = metadata.version(dep.name)
        return f"{dep.name}=={version}"
    except metadata.PackageNotFoundError:
        return dep.fallback


def build_contents() -> str:
    lines: list[str] = [
        "# Requisitos del ERP VAH",
        "# Archivo generado automaticamente por scripts/generar_requirements_erp.py",
        "# Las dependencias instaladas se fijan con ==; las faltantes usan un rango compatible.",
        "",
    ]

    sections = ("Runtime", "Optional", "Build")
    for section in sections:
        lines.append(f"# {section}")
        for dep in DEPENDENCIES:
            if dep.section == section:
                lines.append(resolve_requirement(dep))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    target = root / "requirements.txt"
    target.write_text(build_contents(), encoding="utf-8")
    print(f"requirements.txt actualizado: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
