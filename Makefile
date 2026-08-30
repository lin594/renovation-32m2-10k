PYTHON ?= python3

.PHONY: check summary

check:
	$(PYTHON) scripts/check_project.py

summary:
	$(PYTHON) scripts/check_project.py --summary
