# experiments/v2/conditions — Experimental Conditions

Definitions of the v2 experimental **conditions** (the arms being compared,
e.g. baseline vs. AFCI, with/without reset), one self-contained spec per
condition.

Each condition definition should make the arm fully reproducible: the context
supplied to the model, the prompt pack used, whether the working tree is reset
between tasks, and any per-condition configuration. In v1 the reset/non-reset
handling was entangled with an accumulating, never-reset working tree
(non-independent runs); v2 conditions must specify independence explicitly.

Add condition specs here (do not fabricate results). No run outputs belong in
this folder.
