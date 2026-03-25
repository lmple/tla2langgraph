---- MODULE EmptyNext ----
VARIABLES x

Init == x = 0

\* Next has only inline (non-named) sub-actions — no named sub-actions to extract
Next == x' = x + 1

====
