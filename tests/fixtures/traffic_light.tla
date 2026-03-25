---- MODULE TrafficLight ----
VARIABLES light

Init == light = "red"

GoGreen  == /\ light = "red"    /\ light' = "green"
GoYellow == /\ light = "green"  /\ light' = "yellow"
GoRed    == /\ light = "yellow" /\ light' = "red"

Next == GoGreen \/ GoYellow \/ GoRed

====
