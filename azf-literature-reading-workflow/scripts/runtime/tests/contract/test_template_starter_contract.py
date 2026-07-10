from pathlib import Path

from workflow.services.template_versions import compatible_template


def test_template_yaml_is_major_version_compatible() -> None:
    path = Path("workflow/templates/paper-workspace/template.yaml")
    assert compatible_template(path)

