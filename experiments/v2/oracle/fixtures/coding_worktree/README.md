# coding_worktree fixture

A representative, conformant snapshot of what the coding model may see. It
contains ONLY application/library source and a tsconfig — NO evaluator manifest,
NO hidden tests, NO expected/prohibited layers, NO legitimate-answer list, and NO
architecture scoring output. `experiments/v2/harness/tests/test_evaluator_mount_policy.py`
asserts this tree is free of every forbidden evaluator artifact
(docs/v2/EVALUATOR_MOUNT_POLICY.md §4).
