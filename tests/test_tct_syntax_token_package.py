import json

import pytest

from nanochat.tct_syntax_token_package import (
    EXPECTED_CONSUMER_INTERFACE,
    EXPECTED_CONSUMER_REPOSITORY,
    check_tct_syntax_token_package,
    token_sequence_fingerprint,
)


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def _write_package(package_dir):
    sequences = [[1, 2, 3], [4, 5]]
    train = [sequences[1]]
    validation = [sequences[0]]
    fingerprint = token_sequence_fingerprint(sequences)
    package_dir.mkdir()

    _write_jsonl(package_dir / "tokens.jsonl", sequences)
    _write_jsonl(package_dir / "train.jsonl", train)
    _write_jsonl(package_dir / "validation.jsonl", validation)
    _write_jsonl(
        package_dir / "sources.jsonl",
        [
            {"sequence_index": 0, "split": "validation"},
            {"sequence_index": 1, "split": "train"},
        ],
    )
    _write_json(
        package_dir / "stats.json",
        {
            "artifact_kind": "tct_syntax_go_real_source_training_corpus_stats",
            "sequence_count": 2,
            "total_tokens": 5,
            "max_token_id": 5,
            "sequence_fingerprint": fingerprint,
        },
    )
    _write_json(
        package_dir / "split.json",
        {
            "artifact_kind": "tct_syntax_go_real_source_training_corpus_split",
            "sequence_count": 2,
            "train_sequence_count": 1,
            "validation_sequence_count": 1,
            "train_sequence_indices": [1],
            "validation_sequence_indices": [0],
            "sequence_fingerprint": fingerprint,
        },
    )
    _write_json(
        package_dir / "consumer-manifest.json",
        {
            "artifact_kind": "tct_syntax_go_real_source_training_corpus_consumer_manifest",
            "status": "ready_for_tct_models_training_handoff",
            "consumer_contract_status": "accepted_by_checked_consumer_contract",
            "expected_consumer_repository": EXPECTED_CONSUMER_REPOSITORY,
            "expected_consumer_interface": EXPECTED_CONSUMER_INTERFACE,
            "consumer_contract_blocker": "",
            "token_jsonl_format": "jsonl_u32_token_array_v1",
            "raw_sequence_policy": "raw syntax-level TCT token sequences; no BOS, EOS, or PAD tokens added by packager",
            "sequence_count": 2,
            "train_sequence_count": 1,
            "validation_sequence_count": 1,
            "token_corpus_fingerprint": fingerprint,
            "blocked_claims": [
                "no_downstream_training_run",
                "no_model_quality_claim",
                "no_paper_facing_claim",
            ],
        },
    )
    _write_json(
        package_dir / "metadata.json",
        {
            "artifact_kind": "tct_syntax_go_real_source_training_corpus_package",
            "token_jsonl_format": "jsonl_u32_token_array_v1",
            "raw_sequence_policy": "raw syntax-level TCT token sequences; no BOS, EOS, or PAD tokens added by packager",
            "base_vocab_size": 6,
            "train_count": 1,
            "validate_count": 1,
            "token_corpus": {
                "sequence_count": 2,
                "total_tokens": 5,
                "max_token_id": 5,
                "sequence_fingerprint": fingerprint,
            },
            "consumer_manifest": {
                "expected_consumer_repository": EXPECTED_CONSUMER_REPOSITORY,
                "consumer_contract_status": "accepted_by_checked_consumer_contract",
                "consumer_contract_blocker": "",
            },
        },
    )


def test_check_tct_syntax_token_package_accepts_validation_split_and_writes_alias(tmp_path):
    package_dir = tmp_path / "package"
    _write_package(package_dir)

    summary = check_tct_syntax_token_package(package_dir, write_validate_alias=True)

    assert summary["ok"] is True
    assert summary["sequence_count"] == 2
    assert summary["validation_jsonl"] == "validation.jsonl"
    assert summary["expected_consumer_repository"] == "../tct-models"
    assert (package_dir / "validate.jsonl").read_text(encoding="utf-8") == (
        package_dir / "validation.jsonl"
    ).read_text(encoding="utf-8")


def test_check_tct_syntax_token_package_rejects_stale_consumer_contract(tmp_path):
    package_dir = tmp_path / "package"
    _write_package(package_dir)
    manifest_path = package_dir / "consumer-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expected_consumer_repository"] = "../old-downstream"
    manifest["blocked_claims"].append("missing_checked_downstream_consumer_contract")
    _write_json(manifest_path, manifest)

    summary = check_tct_syntax_token_package(package_dir)

    assert summary["ok"] is False
    assert any("expected_consumer_repository" in error for error in summary["errors"])
    assert any("missing downstream contract" in error for error in summary["errors"])


def test_jsonl_dataloader_accepts_validation_jsonl_alias(tmp_path):
    pytest.importorskip("torch")
    from nanochat.jsonl_dataloader import _load_all_sequences, _validation_jsonl_path

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_jsonl(data_dir / "train.jsonl", [[1, 2]])
    _write_jsonl(data_dir / "validation.jsonl", [[3, 4]])

    assert _validation_jsonl_path(data_dir).name == "validation.jsonl"
    assert _load_all_sequences(data_dir) == [[1, 2], [3, 4]]
