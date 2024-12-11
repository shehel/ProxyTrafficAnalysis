#!/bin/bash

while true; do
	python3 browse_emu_mixed_simplified.py 120 LOW NO 2
	python3 browse_emu_mixed_simplified.py 120 LOW YES 2
	python3 browse_emu_mixed_simplified.py 120 MEDIUM YES 2
	python3 browse_emu_mixed_simplified.py 120 HIGH YES 2
done
