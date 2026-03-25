---- MODULE SimpleMutex ----
VARIABLES lock

Init == lock = "free"

Acquire == /\ lock = "free"  /\ lock' = "held"
Release  == /\ lock = "held" /\ lock' = "free"

Next == Acquire \/ Release

====
