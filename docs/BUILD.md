# Build from source

## Host tools

Use Linux x86-64, Python 3.10 or newer, `dpkg-deb`, and a Python environment with Pillow. Network access is needed for the initial download of the pinned Debian ARM toolchain packages. The compiler is extracted locally and does not require root privileges.

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-build.txt
python3 scripts/bootstrap-toolchain.py
python3 scripts/build.py
python3 scripts/package.py
```

The installation archive is written to `Installation/`. Generated files and reports are written to `build/`, which is excluded from version control.

`PICN_SKIN_PYTHON` can select another Pillow-enabled Python interpreter. `PICN_SYSROOT` can select an existing compatible toolchain root. Defaults use the active Python interpreter and `toolchain/root`.

The toolchain package names, versions and SHA-256 hashes are pinned in TOOLCHAIN.json. Downloads are checked before extraction. Keep these pins consistent with the required ARM hard-float ABI and target system libraries.

## Build steps

1. Generate the fixed-index parameter model and note table.
2. Verify vendored wrapper and generator hashes.
3. Check `params.lock`; forced parameter relocking is prohibited.
4. Compile C11 for ARMv7 hard-float with NEON and link against the target ALSA runtime.
5. Generate native pages, PNG artwork and Q-Link maps.
6. Record input, ELF and output hashes in `build/reports`.
7. Assemble regular-file portable payloads, verify ZIP contents and write SHA-256 checksums.

The build does not connect to a Force, register a plugin, restart MPC or modify firmware.

## UI illustrations and manual

After building:

```sh
python3 scripts/preview_skin.py
python3 scripts/build_manual.py
```

The manual builder embeds images so USER-MANUAL.html can be opened offline. The Markdown manual remains the editable text source.

## Source rules

Keep UID, binary name, content folder and native skin identifier consistent. Keep parameter indices fixed. Preserve callback bounds and the single MIDI output path. Document format or resource changes in the relevant technical document.

Before distributing a locally rebuilt package, check its behavior on the intended hardware and target routing. Compilation alone cannot establish MIDI timing or target-sampler behavior.
