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
    assert "source_poolside_can: reused_source_visual" in output
    assert "product_wrapper_front: generated_from_product_asset" in output
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
    assert "prompt[product_wrapper_front product-to-source-visual]" in output
    assert "prompt[text_generated text-to-source-visual]" in output
    assert "Do not render text" in output
