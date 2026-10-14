# Strategy registry

`shadow_trials.json`: the list of trials the forward shadow runner evaluates, as
`[{"strategy": "FAILED_BREAK", "params": {...}, "status": "LEAD|CANDIDATE|CHAMPION", "experiment": "EXP-001"}]`.
A trial enters this file only through a registered experiment verdict. It is empty until one does.
