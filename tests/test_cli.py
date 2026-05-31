from creative_automation.cli import main


def test_dry_run_prints_asset_classification(capsys) -> None:
    exit_code = main(
        [
            "--brief",
            "input_examples/briefs/summer_refresh.yaml",
            "--assets",
            "input_examples/assets",
            "--out",
            "outputs",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Campaign: summer_refresh_2026" in output
    assert "sparkling_lemon_water" in output
    assert "text_generated: generated_from_text" in output
    assert "source_citrus_craft_soda_source_visual: reused_source_visual" in output
    assert "product_citrus_craft_soda_product: generated_from_product_asset" in output
    assert "product_peach_black_iced_tea_product: generated_from_product_asset" in output
    assert "text_generated: generated_from_text" in output


def test_dry_run_prints_rule_based_prompts_when_requested(capsys) -> None:
    exit_code = main(
        [
            "--brief",
            "input_examples/briefs/summer_refresh.yaml",
            "--assets",
            "input_examples/assets",
            "--out",
            "outputs",
            "--dry-run",
            "--show-prompts",
            "--prompt-planner",
            "rule-based",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "prompt[product_citrus_craft_soda_product product-to-source-visual]" in output
    assert "prompt[product_peach_black_iced_tea_product product-to-source-visual]" in output
    assert "prompt[text_generated text-to-source-visual]" in output
    assert "Do not render text" in output


def test_cli_prepares_source_visuals_with_mock_generator(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "--brief",
            "input_examples/briefs/summer_refresh.yaml",
            "--assets",
            "input_examples/assets",
            "--out",
            str(tmp_path),
            "--prompt-planner",
            "rule-based",
            "--image-provider",
            "mock",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "prepared=" in output
    assert (
        tmp_path / "summer_refresh_2026" / "citrus_craft_soda" / "product_citrus_craft_soda_product" / "generated_source_visual.png"
    ).exists()
    assert (
        tmp_path / "summer_refresh_2026" / "sparkling_lemon_water" / "text_generated" / "generated_source_visual.png"
    ).exists()
    assert (
        tmp_path / "summer_refresh_2026" / "peach_black_iced_tea" / "product_peach_black_iced_tea_product" / "generated_source_visual.png"
    ).exists()


def test_cli_writes_report_when_requested(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "--brief",
            "input_examples/briefs/summer_refresh.yaml",
            "--assets",
            "input_examples/assets",
            "--out",
            str(tmp_path),
            "--prompt-planner",
            "rule-based",
            "--image-provider",
            "mock",
            "--report",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Report:" in output
    assert (tmp_path / "summer_refresh_2026" / "report.json").exists()


def test_cli_adapts_source_visuals_when_requested(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "--brief",
            "input_examples/briefs/summer_refresh.yaml",
            "--assets",
            "input_examples/assets",
            "--out",
            str(tmp_path),
            "--prompt-planner",
            "rule-based",
            "--image-provider",
            "mock",
            "--adapt-source-visuals",
        ]
    )

    capsys.readouterr()

    assert exit_code == 0
    assert (
        tmp_path
        / "summer_refresh_2026"
        / "sparkling_lemon_water"
        / "text_generated"
        / "16x9_source_visual.png"
    ).exists()
