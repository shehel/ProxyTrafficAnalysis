#!/bin/bash

while true; do
	python3 browse_emu_mixed_simplified.py 240 LOW NO 2
	python3 browse_emu_mixed_simplified.py 240 LOW YES 2
	python3 browse_emu_mixed_simplified.py 240 MEDIUM YES 2
	python3 browse_emu_mixed_simplified.py 240 HIGH YES 2
done
