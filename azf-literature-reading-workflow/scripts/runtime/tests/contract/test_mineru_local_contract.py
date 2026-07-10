from workflow.adapters.mineru_docker import docker_status


def test_docker_status_has_availability_flag() -> None:
    status = docker_status()
    assert "available" in status

