# Fictional documentation-change example

This is an authored illustration, not a diff from a real project.

## Code change

```diff
-def list_items(limit=20):
+def list_items(page_size=20):
```

## Current documentation

```python
list_items(limit=50)
```

Assume the owner has authorized a documentation-only patch. Nothing here authorizes executing the code.
