---
name: documentation-update
description: "Trace a code change into the documentation it affects and prepare a reviewable patch."
---

## Task
Use a bounded code diff to propose documentation changes. Produce a patch the owner can review; do not merge, publish, or change application behavior.

## Inputs
A local repository, an owner-selected base revision and target revision, and the project's contributor instructions. The included examples are fictional text-only samples, not an executed repository change.

## Steps
1. Read the repository's contributor instructions. Record the selected revisions and inspect the working tree without changing it. Preserve unrelated changes.
2. Read the code diff and identify public interfaces or behavior that changed. Separate observed changes from inferred intent.
3. Search the relevant documentation for affected names, examples, flags, and setup instructions. Do not scan unrelated directories or accounts.
4. Map each proposed documentation edit to a specific diff hunk. If intent is unclear, report a question instead of silently documenting a guess.
5. After permission to edit, prepare the smallest documentation-only patch on a separate branch or worktree. Do not reset, overwrite unrelated edits, or modify implementation code.
6. Inspect documented check commands before running them. With appropriate authorization, run the relevant documentation checks in an isolated environment; record real results and unavailable checks.
7. Present the patch, the evidence mapping, and remaining uncertainties. Opening a remote PR, merging, or publishing requires the owner's authorization.

## Outputs
A documentation-only patch, a code-to-documentation mapping, and actual check results with limitations. A written check command is not a passed test.

## Human approval
The owner approves the revision range, edits, command execution, and any remote PR submission. No automatic commits, pushes, merges, or publication are granted by installing this skill.

## Failure modes
A diff may omit the context needed to understand behavior. Generated documentation may require an additional source edit. Existing working-tree changes may overlap. Check commands may execute untrusted project code. Stop when scope or safety is ambiguous.
