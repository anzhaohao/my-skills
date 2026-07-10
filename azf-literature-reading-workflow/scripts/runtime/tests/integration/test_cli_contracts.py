from workflow.cli import build_parser


def test_migrate_concept_cards_cli_matches_command_contract() -> None:
    args = build_parser().parse_args(["migrate-concept-cards"])
    for name in [
        "vault_root",
        "paper_root",
        "target_root",
        "template_target",
        "report_json",
        "report_markdown",
        "staging_root",
        "apply",
        "replace_existing",
        "archive_root",
        "archive_sources",
        "delete_sources",
    ]:
        assert hasattr(args, name)


def test_doctor_supports_strict_readiness() -> None:
    args = build_parser().parse_args(["doctor", "--strict"])
    assert args.strict is True
    assert args.reuse_existing is False


def test_parse_defaults_to_new_docker_parse() -> None:
    args = build_parser().parse_args(["parse-with-mineru", "--workspace", "paper"])
    assert args.mode == "docker-run"


def test_two_round_location_commands_are_available() -> None:
    locate = build_parser().parse_args(["locate"])
    confirm = build_parser().parse_args(["confirm-locations"])
    assert hasattr(locate, "manifest")
    assert hasattr(locate, "registry")
    assert hasattr(confirm, "manifest")


def test_mutating_commands_accept_location_manifest() -> None:
    args = build_parser().parse_args(["generate-deep-reading", "--workspace", "paper", "--title-zh", "测试"])
    assert hasattr(args, "location_manifest")