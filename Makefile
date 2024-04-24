test: test_lint test_unit test_integration

test_lint:
	pre-commit run --all-files --show-diff-on-failure

test_unit:
	pytest -vvv --cov-report term-missing --cov=cartography tests/unit

test_integration:
	pytest -vvv --cov-report term-missing --cov=cartography tests/integration

build_py_pkg:
	python3 -m pip install --upgrade build twine
	python3 -m build
	python3 -m twine check dist/*

clean:
	rm -rf dist

clean_all: clean
	rm -rf .venv
	rm -f Pipfile.lock
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf cartography.egg-info
	rm -rf tests/__pycache__
	rm -rf tests/integration/__pycache__
	rm -rf tests/unit/__pycache__
