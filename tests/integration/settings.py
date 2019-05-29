import os

# URL for cartography integration tests
NEO4J_URL = os.environ["NEO4J_URL"] if "NEO4J_URL" in os.environ else "bolt://localhost:7687"

def get(name):
	return globals().get(name)