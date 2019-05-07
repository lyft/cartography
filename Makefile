test: test_lint test_unit test_integration

test_lint:
	flake8

test_unit:
	pytest tests/unit

test_integration:
	pytest tests/integration
