---
name: econ-knowledge
description: Retrieve local economics knowledge and host-provided domain sources with their required prerequisites. Retain external source bodies and versions in existing task outputs and connect them to research decisions and arguments.
---

# Economics knowledge

The knowledge library supplies the definitions, equations, model conditions and worked examples that step 3 of the [economist's procedure](../../runtime/ECONOMIST.md) needs. Retrieve the determining result before using it. Prefer results delivering the same conclusion under weaker sufficient restrictions, and derive their strongest economic implications under ECONOMIST Economic priority.

```sh
python3 skills/econ-knowledge/scripts/knowledge.py domains
python3 skills/econ-knowledge/scripts/knowledge.py search --query "<economic interaction>" --limit 6
python3 skills/econ-knowledge/scripts/knowledge.py plan UNIT-ID --read --focus
```

The focused view displays the selected model and its prerequisite locators. Save the first result and reuse it; read prerequisites at the stage that uses them. Record the unit IDs in the worksheet. Search, classification and model contracts are described in [retrieval](references/retrieval.md#domains-and-search).

<!-- BEGIN GENERATED MODES -->
## Registered operations

- `lookup`: Retrieve the economics definitions, derivations, model conditions or worked examples needed by the current specialist.
<!-- END GENERATED MODES -->
