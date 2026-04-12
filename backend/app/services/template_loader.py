"""Template loader for company configurations.

Templates define the company type, departments, colors, and tool assignments.
They allow the same agentic framework to be used for any company type.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.config import TEMPLATES_DIR, ACTIVE_TEMPLATE


@dataclass
class DepartmentConfig:
    color: str
    label: str


@dataclass
class TemplateConfig:
    name: str
    description: str
    version: str
    departments: dict[str, DepartmentConfig]
    default_tools: list[str]
    department_tools: dict[str, list[str]]
    agents_dir: Path

    def get_department_color(self, department: str) -> str:
        dept = self.departments.get(department)
        return dept.color if dept else "#6366f1"

    def get_department_label(self, department: str) -> str:
        dept = self.departments.get(department)
        return dept.label if dept else department.title()

    def get_tools_for_department(self, department: str) -> list[str]:
        return self.default_tools + self.department_tools.get(department, [])


def load_template(template_name: str | None = None) -> TemplateConfig:
    """Load a company template configuration."""
    name = template_name or ACTIVE_TEMPLATE
    template_dir = TEMPLATES_DIR / name

    yaml_path = template_dir / "template.yaml"
    if not yaml_path.exists():
        # Fallback: return a default config
        return TemplateConfig(
            name=name,
            description="Default template",
            version="1.0",
            departments={},
            default_tools=[],
            department_tools={},
            agents_dir=template_dir / "agents",
        )

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    departments = {}
    for dept_id, dept_data in data.get("departments", {}).items():
        departments[dept_id] = DepartmentConfig(
            color=dept_data.get("color", "#6366f1"),
            label=dept_data.get("label", dept_id.title()),
        )

    return TemplateConfig(
        name=data.get("name", name),
        description=data.get("description", ""),
        version=data.get("version", "1.0"),
        departments=departments,
        default_tools=data.get("default_tools", []),
        department_tools=data.get("department_tools", {}),
        agents_dir=template_dir / "agents",
    )
