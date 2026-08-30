PYTHON ?= python3
RUBY ?= ruby

.PHONY: check diagrams summary test

diagrams:
	$(PYTHON) scripts/generate_diagrams.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

check:
	$(RUBY) scripts/check_yaml.rb
	$(PYTHON) scripts/check_project.py
	$(MAKE) test

summary:
	$(PYTHON) scripts/check_project.py --summary
