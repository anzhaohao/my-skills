from workflow.adapters.figure_render_extractor import SKILL_ROOT
from workflow.adapters.mineru_docker import docker_status


def test_docker_status_has_availability_flag() -> None:
    status = docker_status()
    assert "available" in status


def test_figure_extractor_uses_canonical_azf_skill_directory() -> None:
    assert SKILL_ROOT.name == "azf-pdf-figure-render-extractor"
