test: test_lint test_unit

test_lint:
	flake8

test_unit:
	pytest tests/unit
