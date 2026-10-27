# Release 1.2.4

- Reduce unnecessary display work when selecting lanes and changing lane controls. PATTERN no longer invalidates the complete MOD visual snapshot; MOD retains its independent selection and updates.
- Fix CONFIG heading alignment: PAD, MODE and MIDI NOTE share a baseline and use the same native font and size as PATTERN parameter labels. MODE remains centered over GATE / HOLD.

Validated on Akai Force: the reported touchscreen-related audio crackles were resolved in the tested project. MIDI scheduling and stored musical settings are unchanged by the display fix.
