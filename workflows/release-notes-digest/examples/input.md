# Synthetic release snapshots

These are invented test data, not releases of a real product. No network access is needed.

```json
{
  "previously_reviewed": [
    "sample-v1.0"
  ],
  "releases": [
    {
      "id": "sample-v1.0",
      "source": "Synthetic snapshot A in this fixture",
      "notes": [
        "Adds CSV import."
      ]
    },
    {
      "id": "sample-v1.1",
      "source": "Synthetic snapshot B in this fixture",
      "notes": [
        "Adds a preview-only mode that makes no writes.",
        "Renames the --timeout flag to --request-timeout. Update invocations using the old flag."
      ]
    }
  ]
}
```
