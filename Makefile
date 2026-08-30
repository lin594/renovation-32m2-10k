PYTHON ?= python3
RUBY ?= ruby

.PHONY: check summary

check:
	$(RUBY) scripts/check_yaml.rb
	$(PYTHON) scripts/check_project.py

summary:
	$(PYTHON) scripts/check_project.py --summary
