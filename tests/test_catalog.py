import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.catalog import load_workflows


class CatalogTests(unittest.TestCase):
    def _write_valid_workflow(self, root: Path, workflow_id: str = "research-notes") -> None:
        workflow = root / "workflows" / workflow_id
        (workflow / "examples").mkdir(parents=True)
        (workflow / "workflow.json").write_text(
            json.dumps(
                {
                    "id": workflow_id,
                    "title": "Research notes",
                    "summary": "Turn a question into grounded notes.",
                    "version": "1.0.0",
                    "category": "research",
                    "tags": ["research", "notes"],
                    "requirements": ["A question"],
                    "permissions": [],
                    "outputs": ["A Markdown note"],
                    "authors": ["Community contributor"],
                    "license": "MIT",
                    "status": "draft",
                    "evidence": None,
                }
            ),
            encoding="utf-8",
        )
        (workflow / "SKILL.md").write_text(
            f"""---
name: {workflow_id}
description: Turn a question into grounded notes.
---

## Task
Turn a question into grounded notes.

## Steps
1. Gather sources.

## Inputs
A question.

## Outputs
A Markdown note.

## Human approval
Review the note.

## Failure modes
Stop when sources are unavailable.
""",
            encoding="utf-8",
        )
        (workflow / "examples" / "input.md").write_text("# Question\n", encoding="utf-8")
        (workflow / "examples" / "output.md").write_text("# Notes\n", encoding="utf-8")

    def _write_fixture_workflow(self, root: Path) -> None:
        self._write_valid_workflow(root)
        workflow = root / "workflows" / "research-notes"
        metadata_path = workflow / "workflow.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["status"] = "fixture-tested"
        metadata["evidence"] = "evidence/run.json"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        evidence = workflow / "evidence"
        evidence.mkdir()
        (evidence / "run.json").write_text(
            json.dumps(
                {
                    "kind": "local-fixture",
                    "command": "fixture command is declaration only",
                    "outcome": "pass",
                    "limitations": ["Synthetic fixture only."],
                    "artifacts": ["SKILL.md", "examples/input.md"],
                }
            ),
            encoding="utf-8",
        )

    def test_loads_fixture_tested_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_fixture_workflow(root)

            result = load_workflows(root)

            self.assertEqual(result[0]["status"], "fixture-tested")
            self.assertEqual(result[0]["evidence"], "evidence/run.json")

    def test_rejects_unsafe_or_missing_evidence_artifacts(self) -> None:
        for artifact in ("../outside.md", "/tmp/outside.md", "examples/missing.md"):
            with self.subTest(artifact=artifact):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self._write_fixture_workflow(root)
                    evidence_path = root / "workflows" / "research-notes" / "evidence" / "run.json"
                    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                    evidence["artifacts"] = [artifact]
                    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

                    with self.assertRaisesRegex(ValueError, r"artifact|missing"):
                        load_workflows(root)

    def test_loads_valid_workflow_and_returns_catalog_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)

            result = load_workflows(root)

            self.assertEqual(len(result), 1)
            self.assertEqual(
                set(result[0]),
                {
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
                    "instructions",
                    "example_input",
                    "example_output",
                },
            )
            self.assertEqual(result[0]["id"], "research-notes")
            self.assertEqual(result[0]["instructions"].splitlines()[0], "---")
            self.assertEqual(result[0]["example_input"], "# Question\n")
            self.assertEqual(result[0]["example_output"], "# Notes\n")

    def test_returns_workflows_sorted_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root, "zeta")
            self._write_valid_workflow(root, "alpha")

            result = load_workflows(root)

            self.assertEqual([workflow["id"] for workflow in result], ["alpha", "zeta"])

    def test_rejects_metadata_with_extra_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            metadata_path = root / "workflows" / "research-notes" / "workflow.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["unexpected"] = True
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"keys.*workflow\.json"):
                load_workflows(root)

    def test_metadata_key_error_names_missing_and_extra_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            path = root / "workflows" / "research-notes" / "workflow.json"
            metadata = json.loads(path.read_text())
            del metadata["permissions"]
            metadata["invented"] = True
            path.write_text(json.dumps(metadata))
            with self.assertRaises(ValueError) as caught:
                load_workflows(root)
            self.assertIn("missing: permissions", str(caught.exception))
            self.assertIn("unexpected: invented", str(caught.exception))

    def test_rejects_malformed_metadata_with_path_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            metadata_path = root / "workflows" / "research-notes" / "workflow.json"
            metadata_path.write_text("{", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"workflow\.json"):
                load_workflows(root)

    def test_rejects_oversized_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            metadata_path = root / "workflows" / "research-notes" / "workflow.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["title"] = "x" * (64 * 1024)
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"too large.*workflow\.json"):
                load_workflows(root)

    def test_rejects_oversized_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            oversized = root / "workflows" / "research-notes" / "examples" / "input.md"
            oversized.write_text("x" * (256 * 1024 + 1), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"too large.*input\.md"):
                load_workflows(root)

    def test_rejects_empty_markdown_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            empty = root / "workflows" / "research-notes" / "examples" / "input.md"
            empty.write_text("", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"empty.*input\.md"):
                load_workflows(root)

    def test_rejects_skill_without_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            skill_path = root / "workflows" / "research-notes" / "SKILL.md"
            skill = skill_path.read_text(encoding="utf-8").replace("## Inputs", "## Context")
            skill_path.write_text(skill, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"SKILL\.md.*Inputs"):
                load_workflows(root)

    def test_rejects_markdown_event_handler_scripting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            skill_path = root / "workflows" / "research-notes" / "SKILL.md"
            skill = skill_path.read_text(encoding="utf-8").replace(
                "## Inputs", "## Inputs\n<img src=x onerror=alert(1)>"
            )
            skill_path.write_text(skill, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"scripting.*SKILL\.md"):
                load_workflows(root)

    def test_rejects_missing_required_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            missing = root / "workflows" / "research-notes" / "examples" / "output.md"
            missing.unlink()

            with self.assertRaisesRegex(ValueError, r"output\.md"):
                load_workflows(root)

    def test_rejects_invalid_metadata_values(self) -> None:
        invalid_values = {
            "title": None,
            "summary": "",
            "version": "1.0.0-beta",
            "category": "other",
            "tags": [],
            "requirements": [7],
            "permissions": [""],
            "outputs": [],
            "authors": [],
            "license": "Apache-2.0",
            "status": "published",
            "evidence": "evidence/run.json",
        }
        for field, invalid_value in invalid_values.items():
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    self._write_valid_workflow(root)
                    metadata_path = root / "workflows" / "research-notes" / "workflow.json"
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    metadata[field] = invalid_value
                    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

                    with self.assertRaises(ValueError):
                        load_workflows(root)

    def test_rejects_unexpected_contributor_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            unexpected = root / "workflows" / "research-notes" / "run.py"
            unexpected.write_text("print('do not run')", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"unexpected.*run\.py"):
                load_workflows(root)

    def test_rejects_symlinked_required_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            skill_path = root / "workflows" / "research-notes" / "SKILL.md"
            target = root / "safe-skill.md"
            target.write_text(skill_path.read_text(encoding="utf-8"), encoding="utf-8")
            skill_path.unlink()
            os.symlink(target, skill_path)

            with self.assertRaisesRegex(ValueError, r"symlink.*SKILL\.md"):
                load_workflows(root)

    def test_rejects_symlinked_workflow_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target_root = root / "target"
            self._write_valid_workflow(target_root)
            (root / "workflows").mkdir()
            os.symlink(target_root / "workflows" / "research-notes", root / "workflows" / "research-notes")

            with self.assertRaisesRegex(ValueError, r"symlink"):
                load_workflows(root)

    def test_rejects_non_directory_workflow_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "workflows").mkdir()
            (root / "workflows" / "not-a-workflow").write_text("nope", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"not-a-workflow"):
                load_workflows(root)

    def test_rejects_id_that_is_not_lower_kebab_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            metadata_path = root / "workflows" / "research-notes" / "workflow.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["id"] = "Research_Notes"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"id.*lower-case kebab"):
                load_workflows(root)

    def test_rejects_duplicate_metadata_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            metadata_path = root / "workflows" / "research-notes" / "workflow.json"
            metadata = metadata_path.read_text(encoding="utf-8")
            duplicate = '"id": "research-notes", "id": "other",'
            metadata_path.write_text(metadata.replace('"id": "research-notes",', duplicate), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"duplicate.*id"):
                load_workflows(root)

    def test_rejects_missing_or_empty_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            with self.assertRaisesRegex(ValueError, r"workflows"):
                load_workflows(root)

            (root / "workflows").mkdir()
            with self.assertRaisesRegex(ValueError, r"empty"):
                load_workflows(root)

    def test_cli_check_reports_validity_and_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_valid_workflow(root)
            script = Path(__file__).resolve().parents[1] / "tools" / "catalog.py"
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            valid = subprocess.run(
                [sys.executable, str(script), "check", "--root", str(root)],
                cwd=str(script.parents[1]),
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertEqual(
                json.loads(valid.stdout), {"valid": True, "workflow_count": 1}
            )

            (root / "workflows" / "research-notes" / "workflow.json").write_text(
                "{", encoding="utf-8"
            )
            invalid = subprocess.run(
                [sys.executable, str(script), "check", "--root", str(root)],
                cwd=str(script.parents[1]),
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("workflow.json", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
