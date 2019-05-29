import os

NEO4J_URL = os.environ.get("NEO4J_URL", "bolt://localhost:7687")


def get(name):
    return globals().get(name)
