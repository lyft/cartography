test: test_lint test_unit test_integration

test_lint:
	flake8

test_unit:
	pytest --cov=cartography tests/unit

test_integration:
	pytest --cov=cartography tests/integration
