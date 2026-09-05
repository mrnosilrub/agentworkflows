# Contribute a workflow

Share a reusable way to finish a job—not a transcript or a list of prompts. People and agents use the same contribution format and review process.

## Start with an existing workflow
Search the catalog for the task. Improving an existing workflow is often more useful than adding a near-duplicate. Read its skill and examples before proposing edits.

## Add a new workflow
1. Once the repository is public, fork it and create a contribution branch. This local build has no public remote yet. Rehearsing in a separate local copy is supported now.
2. Copy the template directory into workflows/your-task-name. Use a lower-case kebab-case name.
3. Update workflow.json: use the same id, give the task a plain-English title, list tools and access required, and declare authorship. Start with status draft and evidence null.
4. Update SKILL.md. Its frontmatter name must match id and its description must exactly match summary. Include Task, Inputs, Steps, Outputs, Human approval, and Failure modes sections.
5. Replace examples/input.md and examples/output.md with a small permission-cleared example. Label fictional samples and outputs that were only illustrated. Never present an authored example as an executed result.
6. Run the structural check below. It reads contribution data; it does not execute skill instructions or commands in evidence records.

```sh
python3 -I tools/catalog.py check
```

## Check and preview your change

```sh
python3 -m unittest discover -s tests -v
python3 tools/build.py
python3 -m http.server 8788 --bind 127.0.0.1 --directory dist
```

These commands run repository-maintainer code. Review and trust the repository code before running it; schema validation does not make code from an unfamiliar fork trustworthy. The preview binds to 127.0.0.1 and serves only the generated dist directory.

## Allowed contribution files
The first version accepts workflow.json, SKILL.md, examples/*.md, and evidence/run.json only. No symlinks, executable scripts, dependency installers, raw HTML behavior, credentials, private session logs, or bundled binaries. Each Markdown file is limited to 256 KiB and JSON to 64 KiB. Source URLs can be written as plain text; builds do not fetch them.

## Evidence is not a badge of safety
Use fixture-tested only after a real local fixture check produces preserved artifacts. Add evidence/run.json with kind local-fixture, the actual command, outcome pass, nonempty limitations, and artifact paths relative to the workflow directory. The artifacts must exist. The schema checks the shape and paths, not whether the claimed run happened, whether an author is who they say they are, or whether the workflow is safe. Reviewers inspect those claims separately. The website calls this Example checked; it is not independent certification.

## Submit a pull request
Describe the task and intended user, why it differs from existing workflows, the source and permission status of examples, what you actually ran, what remains untested, and whether an agent assisted. An agent must have its operator's permission before sending a PR or comment. No auto-merge or automatic workflow execution is granted. The maintainer reviews contributions before accepting them.

## Maintainer validation before acceptance
Automatic pull-request jobs are disabled in this initial version. From an existing trusted base copy, run the data-only check against a separate proposed copy:

```sh
python3 -I tools/catalog.py check --root /path/to/proposed-copy
```

Do not run the proposed copy's validator, tests, build, or installers. Tooling changes need separate code review. Main-branch CI runs after acceptance; it is not a substitute for this review.

## Licensing and attribution
By submitting original material, you offer it under this repository's MIT license. Keep required attribution and do not submit material you cannot license. Identify the accountable contributor or operator; an agent label alone is not verified human identity. Avoid raw private transcripts, even if they seem relevant. Report sensitive security concerns without posting exploit secrets or private data publicly.
