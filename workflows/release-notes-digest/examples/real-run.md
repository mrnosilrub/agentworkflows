# A real release-notes run

An agent used this library's release-notes workflow to turn official Python release notes into a sourced draft. Here is what it was given, what it returned, and what happened when a source was missing.

This is a historical demonstration using workflow version `0.1.1`, run by an agent working on this project—not an outside user or a claim of community adoption. It is not current upgrade advice. The guide remains a draft; a person still has to review the result.

## The job

Compare the official Python 3.12.1 and 3.12.2 release pages and changelogs with the list of releases already reviewed. Draft an update for anything unseen. Do not install an upgrade, send the draft, or change the reviewed list.

- Already reviewed: `python-3.12.1`.
- Candidate releases: `python-3.12.1` and `python-3.12.2`.
- Output requested: a local digest with sources, compatibility changes, and open questions.

## What the agent returned

The digest excluded `python-3.12.1` and covered only `python-3.12.2`. These excerpts from the actual draft were checked against the official sources:

- The release page dates Python 3.12.2 to February 6, 2024 and describes it as the second maintenance release of Python 3.12, with more than 350 bugfixes, build improvements, and documentation changes since 3.12.1. [Release page](https://www.python.org/downloads/release/python-3122/).
- Socket validation in `asyncio.create_datagram_endpoint()` accepts all non-stream sockets, fixing a raw-socket compatibility regression. [Final changelog](https://docs.python.org/release/3.12.2/whatsnew/changelog.html#python-3-12-2-final), [issue 114887](https://github.com/python/cpython/issues/114887).
- The bundled pip was updated to 24.0. [Final changelog](https://docs.python.org/release/3.12.2/whatsnew/changelog.html#python-3-12-2-final), [issue 114965](https://github.com/python/cpython/issues/114965).

The draft did not turn those changes into a universal upgrade recommendation. It asked whether the target project uses the affected APIs and has tests for those behaviors: release notes alone cannot answer that.

## When a source was missing

In a separate, deliberate failure test, the agent was given a nonexistent detailed-changelog URL on the official documentation host. That request returned HTTP 404. This was a controlled missing-source test, not an outage of the real changelog linked above.

The resulting draft marked coverage **partial**. It retained the release-page summary but withheld issue-level compatibility, security, and maintenance details. It explicitly left a verification gap for human review instead of inventing the missing material.

## What stayed under human control

The reviewed list remained exactly `python-3.12.1` in both runs. The workflow run did not install, send, publish, or schedule anything. Source and instruction hashes were checked; that verifies the material used, not every possible use of the workflow.

This shows a bounded job completed with useful evidence and an honest gap—not autonomous approval or a guarantee of correctness.

## Try it yourself

[Open the workflow](/workflows/release-notes-digest/) and give your agent a public release source plus the release IDs you have already reviewed. Check the draft before approving any next action. If a step is unclear or missing, [contribute an improvement](/contribute/).
