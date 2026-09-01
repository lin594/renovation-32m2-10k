PYTHON ?= python3
RUBY ?= ruby

.PHONY: check diagrams gallery status summary test

diagrams:
	$(PYTHON) scripts/generate_diagrams.py

gallery:
	$(PYTHON) scripts/photo.py gallery

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

status:
	$(RUBY) scripts/generate_status.rb

check: status
	$(RUBY) scripts/check_yaml.rb
	$(PYTHON) scripts/check_project.py
	$(MAKE) test

summary:
	$(PYTHON) scripts/check_project.py --summary
