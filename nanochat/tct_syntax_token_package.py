"""Validation for TCT syntax-token training package handoffs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


CHECK_ARTIFACT_TYPE = "tct_models_syntax_token_package_check"
CHECK_VERSION = 1
PACKAGE_ARTIFACT_KIND = "tct_syntax_go_real_source_training_corpus_package"
CONSUMER_MANIFEST_ARTIFACT_KIND = "tct_syntax_go_real_source_training_corpus_consumer_manifest"
EXPECTED_CONSUMER_REPOSITORY = "../tct-models"
EXPECTED_CONSUMER_INTERFACE = "tct-models raw syntax-token JSONL training package v1"
EXPECTED_CONSUMER_STATUS = "accepted_by_checked_consumer_contract"
EXPECTED_MANIFEST_STATUS = "ready_for_tct_models_training_handoff"
TOKEN_JSONL_FORMAT = "jsonl_u32_token_array_v1"
RAW_SEQUENCE_POLICY = "raw syntax-level TCT token sequences; no BOS, EOS, or PAD tokens added by packager"


def check_tct_syntax_token_package(
    package_dir: str | Path,
    *,
    write_validate_alias: bool = False,
) -> dict[str, Any]:
    """Validate a TCT syntax-token package against the tct-models raw-token contract."""
    package_dir = Path(package_dir)
    errors: list[str] = []

    metadata = _read_json(package_dir / "metadata.json", errors, "metadata.json")
    manifest = _read_json(package_dir / "consumer-manifest.json", errors, "consumer-manifest.json")
    stats = _read_json(package_dir / "stats.json", errors, "stats.json")
    split = _read_json(package_dir / "split.json", errors, "split.json")

    token_sequences = _read_token_jsonl(package_dir / "tokens.jsonl", errors, "tokens.jsonl")
    train_sequences = _read_token_jsonl(package_dir / "train.jsonl", errors, "train.jsonl")
    validation_path = package_dir / "validation.jsonl"
    if not validation_path.exists():
        validation_path = package_dir / "validate.jsonl"
    validation_sequences = _read_token_jsonl(validation_path, errors, validation_path.name)
    source_records = _read_jsonl(package_dir / "sources.jsonl", errors, "sources.jsonl")

    if write_validate_alias:
        alias = package_dir / "validate.jsonl"
        source = package_dir / "validation.jsonl"
        if source.exists() and not alias.exists():
            shutil.copyfile(source, alias)

    if metadata:
        _require_equal(errors, "metadata.artifact_kind", metadata.get("artifact_kind"), PACKAGE_ARTIFACT_KIND)
        _require_equal(errors, "metadata.token_jsonl_format", metadata.get("token_jsonl_format"), TOKEN_JSONL_FORMAT)
        _require_equal(errors, "metadata.raw_sequence_policy", metadata.get("raw_sequence_policy"), RAW_SEQUENCE_POLICY)
        _require_positive_int(errors, "metadata.base_vocab_size", metadata.get("base_vocab_size"))
        _require_positive_int(errors, "metadata.train_count", metadata.get("train_count"))
        _require_positive_int(errors, "metadata.validate_count", metadata.get("validate_count"))
        consumer_summary = metadata.get("consumer_manifest") or {}
        _require_equal(
            errors,
            "metadata.consumer_manifest.expected_consumer_repository",
            consumer_summary.get("expected_consumer_repository"),
            EXPECTED_CONSUMER_REPOSITORY,
        )
        _require_equal(
            errors,
            "metadata.consumer_manifest.consumer_contract_status",
            consumer_summary.get("consumer_contract_status"),
            EXPECTED_CONSUMER_STATUS,
        )
        if consumer_summary.get("consumer_contract_blocker"):
            errors.append("metadata.consumer_manifest.consumer_contract_blocker must be empty")

    if manifest:
        _require_equal(
            errors,
            "consumer_manifest.artifact_kind",
            manifest.get("artifact_kind"),
            CONSUMER_MANIFEST_ARTIFACT_KIND,
        )
        _require_equal(errors, "consumer_manifest.status", manifest.get("status"), EXPECTED_MANIFEST_STATUS)
        _require_equal(
            errors,
            "consumer_manifest.consumer_contract_status",
            manifest.get("consumer_contract_status"),
            EXPECTED_CONSUMER_STATUS,
        )
        _require_equal(
            errors,
            "consumer_manifest.expected_consumer_repository",
            manifest.get("expected_consumer_repository"),
            EXPECTED_CONSUMER_REPOSITORY,
        )
        _require_equal(
            errors,
            "consumer_manifest.expected_consumer_interface",
            manifest.get("expected_consumer_interface"),
            EXPECTED_CONSUMER_INTERFACE,
        )
        if manifest.get("consumer_contract_blocker"):
            errors.append("consumer_manifest.consumer_contract_blocker must be empty")
        _require_equal(errors, "consumer_manifest.token_jsonl_format", manifest.get("token_jsonl_format"), TOKEN_JSONL_FORMAT)
        _require_equal(errors, "consumer_manifest.raw_sequence_policy", manifest.get("raw_sequence_policy"), RAW_SEQUENCE_POLICY)
        blocked_claims = manifest.get("blocked_claims") or []
        if "missing_checked_downstream_consumer_contract" in blocked_claims:
            errors.append("consumer_manifest.blocked_claims still records missing downstream contract")
        if "no_downstream_training_run" not in blocked_claims:
            errors.append("consumer_manifest.blocked_claims must preserve no_downstream_training_run")

    sequence_count = len(token_sequences)
    train_count = len(train_sequences)
    validation_count = len(validation_sequences)
    total_tokens = sum(len(sequence) for sequence in token_sequences)
    max_token_id = max((max(sequence) for sequence in token_sequences if sequence), default=-1)
    fingerprint = token_sequence_fingerprint(token_sequences)

    if stats:
        _require_equal(errors, "stats.sequence_count", stats.get("sequence_count"), sequence_count)
        _require_equal(errors, "stats.total_tokens", stats.get("total_tokens"), total_tokens)
        _require_equal(errors, "stats.max_token_id", stats.get("max_token_id"), max_token_id)
        _require_equal(errors, "stats.sequence_fingerprint", stats.get("sequence_fingerprint"), fingerprint)

    if metadata:
        token_corpus = metadata.get("token_corpus") or {}
        _require_equal(errors, "metadata.token_corpus.sequence_count", token_corpus.get("sequence_count"), sequence_count)
        _require_equal(errors, "metadata.token_corpus.total_tokens", token_corpus.get("total_tokens"), total_tokens)
        _require_equal(errors, "metadata.token_corpus.max_token_id", token_corpus.get("max_token_id"), max_token_id)
        _require_equal(errors, "metadata.token_corpus.sequence_fingerprint", token_corpus.get("sequence_fingerprint"), fingerprint)
        base_vocab_size = metadata.get("base_vocab_size")
        if isinstance(base_vocab_size, int) and max_token_id >= base_vocab_size:
            errors.append("metadata.base_vocab_size must be greater than every token id")
        _require_equal(errors, "metadata.train_count", metadata.get("train_count"), train_count)
        _require_equal(errors, "metadata.validate_count", metadata.get("validate_count"), validation_count)

    if split:
        train_indices = _int_list(split.get("train_sequence_indices"), "split.train_sequence_indices", errors)
        validation_indices = _int_list(split.get("validation_sequence_indices"), "split.validation_sequence_indices", errors)
        _require_equal(errors, "split.sequence_count", split.get("sequence_count"), sequence_count)
        _require_equal(errors, "split.train_sequence_count", split.get("train_sequence_count"), train_count)
        _require_equal(errors, "split.validation_sequence_count", split.get("validation_sequence_count"), validation_count)
        _require_equal(errors, "split.sequence_fingerprint", split.get("sequence_fingerprint"), fingerprint)
        if train_sequences != _select(token_sequences, train_indices, errors, "split.train_sequence_indices"):
            errors.append("train.jsonl does not match split.train_sequence_indices")
        if validation_sequences != _select(token_sequences, validation_indices, errors, "split.validation_sequence_indices"):
            errors.append(f"{validation_path.name} does not match split.validation_sequence_indices")

    if manifest:
        _require_equal(errors, "consumer_manifest.sequence_count", manifest.get("sequence_count"), sequence_count)
        _require_equal(errors, "consumer_manifest.train_sequence_count", manifest.get("train_sequence_count"), train_count)
        _require_equal(errors, "consumer_manifest.validation_sequence_count", manifest.get("validation_sequence_count"), validation_count)
        _require_equal(errors, "consumer_manifest.token_corpus_fingerprint", manifest.get("token_corpus_fingerprint"), fingerprint)

    if source_records and len(source_records) != sequence_count:
        errors.append("sources.jsonl record count must match tokens.jsonl sequence count")

    return {
        "artifact_type": CHECK_ARTIFACT_TYPE,
        "version": CHECK_VERSION,
        "ok": not errors,
        "package_dir": str(package_dir),
        "sequence_count": sequence_count,
        "train_sequence_count": train_count,
        "validation_sequence_count": validation_count,
        "validation_jsonl": validation_path.name,
        "total_tokens": total_tokens,
        "max_token_id": max_token_id,
        "base_vocab_size": metadata.get("base_vocab_size") if metadata else None,
        "token_corpus_fingerprint": fingerprint,
        "expected_consumer_repository": EXPECTED_CONSUMER_REPOSITORY,
        "expected_consumer_interface": EXPECTED_CONSUMER_INTERFACE,
        "errors": errors,
    }


def token_sequence_fingerprint(sequences: list[list[int]]) -> str:
    payload = bytearray(b"tct-bpe-token-corpus-v1\n")
    for sequence in sequences:
        payload.extend(str(len(sequence)).encode("ascii"))
        payload.extend(b":")
        for token in sequence:
            payload.extend(str(token).encode("ascii"))
            payload.extend(b",")
        payload.extend(b"\n")
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        errors.append(f"{label} is missing")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def _read_jsonl(path: Path, errors: list[str], label: str) -> list[Any]:
    records = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    errors.append(f"{label}:{line_number}: invalid JSON: {exc}")
    except FileNotFoundError:
        errors.append(f"{label} is missing")
    return records


def _read_token_jsonl(path: Path, errors: list[str], label: str) -> list[list[int]]:
    records = _read_jsonl(path, errors, label)
    sequences: list[list[int]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, list) or not record:
            errors.append(f"{label}:{index}: token sequence must be a non-empty JSON array")
            continue
        sequence = []
        for token in record:
            if not isinstance(token, int) or token < 0:
                errors.append(f"{label}:{index}: token ids must be non-negative integers")
                sequence = []
                break
            sequence.append(token)
        if sequence:
            sequences.append(sequence)
    return sequences


def _select(sequences: list[list[int]], indices: list[int], errors: list[str], label: str) -> list[list[int]]:
    selected = []
    for index in indices:
        if not (0 <= index < len(sequences)):
            errors.append(f"{label} contains out-of-range index {index}")
            continue
        selected.append(sequences[index])
    return selected


def _int_list(value: Any, label: str, errors: list[str]) -> list[int]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    result = []
    for item in value:
        if not isinstance(item, int) or item < 0:
            errors.append(f"{label} must contain non-negative integers")
            return []
        result.append(item)
    return result


def _require_equal(errors: list[str], field: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        errors.append(f"{field}: expected {expected!r}, got {actual!r}")


def _require_positive_int(errors: list[str], field: str, value: Any) -> None:
    if not isinstance(value, int) or value <= 0:
        errors.append(f"{field} must be a positive integer")
