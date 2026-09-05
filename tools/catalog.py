"""Validate and load the strictly data-only workflow catalog."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_VERSION_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z"
)
_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*\Z")
_UNSAFE_MARKDOWN_PATTERN = re.compile(
    r"<\s*script\b|javascript\s*:|vbscript\s*:|\bon[a-z][a-z0-9_-]*\s*=",
    flags=re.IGNORECASE,
)
_CATEGORIES = {"research", "development", "operations"}
_STATUSES = {"draft", "fixture-tested"}
_METADATA_KEYS = (
    "id",
    "title",
    "summary",
    "version",
    "category",
    "tags",
    "requirements",
    "permissions",
    "outputs",
    "authors",
    "license",
    "status",
    "evidence",
)
_EVIDENCE_KEYS = ("kind", "command", "outcome", "limitations", "artifacts")
_RETURN_KEYS = _METADATA_KEYS + ("instructions", "example_input", "example_output")
_ALLOWED_TOP_LEVEL_FILES = {"workflow.json", "SKILL.md"}
_REQUIRED_EXAMPLES = {"input.md", "output.md"}
_MAX_METADATA_BYTES = 64 * 1024
_MAX_MARKDOWN_BYTES = 256 * 1024


class _DuplicateKey(ValueError):
    """Internal marker retaining the duplicate JSON key."""


def _reject_duplicate_pairs(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value!r} is not allowed")


def _parse_json(text: str, path: Path) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite,
        )
    except ValueError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error


def _lstat(path: Path, *, missing_message: str) -> os.stat_result:
    try:
        return path.lstat()
    except FileNotFoundError as error:
        raise ValueError(f"{missing_message}: {path}") from error
    except OSError as error:
        raise ValueError(f"could not inspect path {path}") from error


def _regular_stat(path: Path, *, missing_message: str = "missing required file") -> os.stat_result:
    info = _lstat(path, missing_message=missing_message)
    if stat.S_ISLNK(info.st_mode):
        raise ValueError(f"symlink is not allowed: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"path is not a regular file: {path}")
    if info.st_mode & 0o111:
        raise ValueError(f"executable files are not allowed: {path}")
    return info


def _require_directory(path: Path, *, missing_message: str = "missing required directory") -> None:
    info = _lstat(path, missing_message=missing_message)
    if stat.S_ISLNK(info.st_mode):
        raise ValueError(f"symlink is not allowed: {path}")
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError(f"path is not a directory: {path}")


def _reject_symlink(path: Path) -> None:
    info = _lstat(path, missing_message="missing path")
    if stat.S_ISLNK(info.st_mode):
        raise ValueError(f"symlink is not allowed: {path}")


def _read_utf8(
    path: Path,
    *,
    limit: int,
    label: str,
    nonempty: bool,
) -> str:
    info = _regular_stat(path)
    if info.st_size > limit:
        raise ValueError(f"{label} file is too large: {path}")
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ValueError(f"could not read {label} file {path}") from error
    if len(data) > limit:
        raise ValueError(f"{label} file is too large: {path}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} file is not valid UTF-8: {path}") from error
    if nonempty and not text.strip():
        raise ValueError(f"{label} file is empty: {path}")
    return text


def _read_metadata(path: Path) -> str:
    return _read_utf8(path, limit=_MAX_METADATA_BYTES, label="metadata", nonempty=False)


def _read_markdown(path: Path) -> str:
    return _read_utf8(path, limit=_MAX_MARKDOWN_BYTES, label="Markdown", nonempty=True)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, nonempty: bool) -> bool:
    return (
        isinstance(value, list)
        and (not nonempty or bool(value))
        and all(_nonempty_string(item) for item in value)
    )


def _validate_metadata(metadata: Any, path: Path, directory_name: str) -> None:
    if not isinstance(metadata, dict) or set(metadata) != set(_METADATA_KEYS):
        raise ValueError(f"invalid metadata keys in {path}")

    workflow_id = metadata["id"]
    if not isinstance(workflow_id, str) or not _ID_PATTERN.fullmatch(workflow_id):
        raise ValueError(f"id must be lower-case kebab-case in {path}")
    if workflow_id != directory_name:
        raise ValueError(f"id does not match workflow directory in {path}")

    for field in ("title", "summary"):
        if not _nonempty_string(metadata[field]):
            raise ValueError(f"{field} must be a nonempty string in {path}")
    if not isinstance(metadata["version"], str) or not _VERSION_PATTERN.fullmatch(
        metadata["version"]
    ):
        raise ValueError(f"version must be numeric x.y.z semver in {path}")
    if not isinstance(metadata["category"], str) or metadata["category"] not in _CATEGORIES:
        raise ValueError(f"category is invalid in {path}")

    tags = metadata["tags"]
    if not isinstance(tags, list) or not tags:
        raise ValueError(f"tags must be a nonempty list in {path}")
    if any(not isinstance(tag, str) or not _ID_PATTERN.fullmatch(tag) for tag in tags):
        raise ValueError(f"tags must be lower-case kebab-case in {path}")
    if len(set(tags)) != len(tags):
        raise ValueError(f"tags must be unique in {path}")

    for field in ("requirements", "permissions"):
        if not _string_list(metadata[field], nonempty=False):
            raise ValueError(f"{field} must be a list of nonempty strings in {path}")
    for field in ("outputs", "authors"):
        if not _string_list(metadata[field], nonempty=True):
            raise ValueError(f"{field} must be a nonempty list of nonempty strings in {path}")

    if metadata["license"] != "MIT":
        raise ValueError(f"license must be MIT in {path}")
    if not isinstance(metadata["status"], str) or metadata["status"] not in _STATUSES:
        raise ValueError(f"status is invalid in {path}")
    if metadata["status"] == "draft" and metadata["evidence"] is not None:
        raise ValueError(f"draft evidence must be null in {path}")
    if metadata["status"] == "fixture-tested" and metadata["evidence"] != "evidence/run.json":
        raise ValueError(f"fixture-tested evidence must be evidence/run.json in {path}")


def _has_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _validate_file_entry(path: Path) -> None:
    _regular_stat(path)


def _list_directory(path: Path, *, label: str) -> List[Path]:
    try:
        return list(path.iterdir())
    except OSError as error:
        raise ValueError(f"could not inspect {label} directory {path}") from error


def _validate_workflow_layout(workflow_dir: Path, status: str) -> None:
    entries = _list_directory(workflow_dir, label="workflow")
    for entry in entries:
        _reject_symlink(entry)
        if _has_control_characters(entry.name):
            raise ValueError(f"control character in path: {entry}")
        if entry.name in _ALLOWED_TOP_LEVEL_FILES:
            _validate_file_entry(entry)
        elif entry.name in {"examples", "evidence"}:
            _require_directory(entry)
        else:
            raise ValueError(f"unexpected file or directory in workflow: {entry}")

    _validate_file_entry(workflow_dir / "workflow.json")
    _validate_file_entry(workflow_dir / "SKILL.md")

    examples_dir = workflow_dir / "examples"
    _require_directory(examples_dir)
    examples = _list_directory(examples_dir, label="examples")
    names = set()
    for example in examples:
        _reject_symlink(example)
        if _has_control_characters(example.name) or not example.name.endswith(".md"):
            raise ValueError(f"unexpected example file: {example}")
        _validate_file_entry(example)
        _read_markdown(example)
        names.add(example.name)
    for required_name in sorted(_REQUIRED_EXAMPLES - names):
        raise ValueError(f"missing required file: {examples_dir / required_name}")

    evidence_dir = workflow_dir / "evidence"
    try:
        evidence_info = evidence_dir.lstat()
    except FileNotFoundError:
        evidence_info = None
    except OSError as error:
        raise ValueError(f"could not inspect path {evidence_dir}") from error

    if status == "draft":
        if evidence_info is not None:
            raise ValueError(f"draft workflow must not contain evidence: {evidence_dir}")
        return

    _require_directory(evidence_dir)
    evidence = _list_directory(evidence_dir, label="evidence")
    for entry in evidence:
        _reject_symlink(entry)
        if entry.name != "run.json":
            raise ValueError(f"unexpected evidence file: {entry}")
        _validate_file_entry(entry)
    _validate_file_entry(evidence_dir / "run.json")


def _parse_frontmatter_value(raw_value: str, key: str, path: Path) -> str:
    if raw_value.startswith('"'):
        try:
            value = json.loads(raw_value)
        except ValueError as error:
            raise ValueError(f"invalid frontmatter value for {key!r} in {path}") from error
        if not isinstance(value, str):
            raise ValueError(f"frontmatter {key!r} must be a string in {path}")
        return value
    return raw_value


def _validate_skill(text: str, path: Path, workflow_id: str, summary: str) -> None:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"SKILL.md is missing YAML frontmatter: {path}")
    try:
        closing_index = next(index for index in range(1, len(lines)) if lines[index] == "---")
    except StopIteration as error:
        raise ValueError(f"SKILL.md has unterminated YAML frontmatter: {path}") from error

    frontmatter: Dict[str, str] = {}
    for line in lines[1:closing_index]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid YAML frontmatter in {path}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key or _has_control_characters(key) or key in frontmatter:
            raise ValueError(f"invalid or duplicate frontmatter key in {path}")
        value = _parse_frontmatter_value(raw_value, key, path)
        if not _nonempty_string(value):
            raise ValueError(f"frontmatter {key!r} must be nonempty in {path}")
        frontmatter[key] = value

    if "name" not in frontmatter or "description" not in frontmatter:
        raise ValueError(f"frontmatter needs name and description in {path}")
    if frontmatter["name"] != workflow_id:
        raise ValueError(f"frontmatter name does not match id in {path}")
    if frontmatter["description"] != summary:
        raise ValueError(f"frontmatter description does not match summary in {path}")

    section_positions: Dict[str, int] = {}
    in_fence = False
    for index, line in enumerate(lines[closing_index + 1 :], start=closing_index + 1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _HEADING_PATTERN.match(line)
        if not match:
            continue
        section_name = re.sub(r"\s+#+\s*\Z", "", match.group(1).strip())
        section_positions.setdefault(section_name, index)

    required_sections = ("Task", "Steps", "Inputs", "Outputs", "Human approval", "Failure modes")
    for section in required_sections:
        if section not in section_positions:
            raise ValueError(f"SKILL.md is missing {section} section: {path}")
        start = section_positions[section] + 1
        end = min(
            (
                position
                for position in section_positions.values()
                if position > section_positions[section]
            ),
            default=len(lines),
        )
        if not "\n".join(lines[start:end]).strip():
            raise ValueError(f"SKILL.md {section} section is empty: {path}")

    if _UNSAFE_MARKDOWN_PATTERN.search(text):
        raise ValueError(f"custom Markdown scripting is not allowed in {path}")


def _validate_artifact_path(value: Any, workflow_dir: Path, evidence_path: Path) -> None:
    if not isinstance(value, str) or not value or _has_control_characters(value):
        raise ValueError(f"artifact path must be a relative POSIX path in {evidence_path}")
    if "\\" in value or value.startswith("/") or "//" in value or value.endswith("/"):
        raise ValueError(f"artifact path must be a relative POSIX path in {evidence_path}")
    try:
        relative = PurePosixPath(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid artifact path in {evidence_path}") from error
    if relative.is_absolute() or not relative.parts or any(part in {".", ".."} for part in relative.parts):
        raise ValueError(f"artifact path must not traverse in {evidence_path}")
    candidate = workflow_dir.joinpath(*relative.parts)
    _regular_stat(candidate, missing_message="missing artifact")


def _validate_evidence(workflow_dir: Path) -> None:
    evidence_path = workflow_dir / "evidence" / "run.json"
    evidence = _parse_json(_read_metadata(evidence_path), evidence_path)
    if not isinstance(evidence, dict) or set(evidence) != set(_EVIDENCE_KEYS):
        raise ValueError(f"invalid evidence keys in {evidence_path}")
    if evidence["kind"] != "local-fixture":
        raise ValueError(f"evidence kind must be local-fixture in {evidence_path}")
    if not _nonempty_string(evidence["command"]):
        raise ValueError(f"evidence command must be a nonempty string in {evidence_path}")
    if evidence["outcome"] != "pass":
        raise ValueError(f"evidence outcome must be pass in {evidence_path}")
    if not _string_list(evidence["limitations"], nonempty=True):
        raise ValueError(f"evidence limitations must be a nonempty string list in {evidence_path}")
    artifacts = evidence["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError(f"evidence artifacts must be a nonempty list in {evidence_path}")
    if any(not isinstance(artifact, str) for artifact in artifacts):
        raise ValueError(f"evidence artifacts must be strings in {evidence_path}")
    if len(set(artifacts)) != len(artifacts):
        raise ValueError(f"evidence artifacts must be unique in {evidence_path}")
    for artifact in artifacts:
        _validate_artifact_path(artifact, workflow_dir, evidence_path)


def load_workflows(root: Path) -> List[Dict[str, Any]]:
    """Validate and load all workflows below *root*, sorted by id."""
    try:
        root_path = Path(root)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid catalog root: {root!r}") from error
    _require_directory(root_path, missing_message="missing catalog root")
    workflows_root = root_path / "workflows"
    _require_directory(workflows_root, missing_message="missing workflows directory")
    entries = _list_directory(workflows_root, label="workflows")
    if not entries:
        raise ValueError(f"catalog workflows directory is empty: {workflows_root}")

    loaded: List[Dict[str, Any]] = []
    for workflow_dir in sorted(entries, key=lambda path: path.name):
        _reject_symlink(workflow_dir)
        _require_directory(workflow_dir, missing_message="missing workflow directory")
        if _has_control_characters(workflow_dir.name) or not _ID_PATTERN.fullmatch(workflow_dir.name):
            raise ValueError(f"workflow directory name must be lower-case kebab-case: {workflow_dir}")

        metadata_path = workflow_dir / "workflow.json"
        _regular_stat(metadata_path)
        metadata = _parse_json(_read_metadata(metadata_path), metadata_path)
        _validate_metadata(metadata, metadata_path, workflow_dir.name)
        _validate_workflow_layout(workflow_dir, metadata["status"])

        skill_path = workflow_dir / "SKILL.md"
        instructions = _read_markdown(skill_path)
        _validate_skill(instructions, skill_path, metadata["id"], metadata["summary"])
        example_input = _read_markdown(workflow_dir / "examples" / "input.md")
        example_output = _read_markdown(workflow_dir / "examples" / "output.md")
        if metadata["status"] == "fixture-tested":
            _validate_evidence(workflow_dir)

        result: Dict[str, Any] = {key: metadata[key] for key in _METADATA_KEYS}
        result.update(
            {
                "instructions": instructions,
                "example_input": example_input,
                "example_output": example_output,
            }
        )
        if tuple(result) != _RETURN_KEYS:
            raise AssertionError("internal catalog result shape mismatch")
        loaded.append(result)
    return loaded


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the AgentWorkflows catalog")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check", help="validate workflow data")
    check_parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="catalog root (default: repository root)",
    )
    args = parser.parse_args(argv)
    try:
        workflows = load_workflows(args.root)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, "workflow_count": len(workflows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
