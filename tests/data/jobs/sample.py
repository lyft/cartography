SAMPLE_CLEANUP_JOB = """
{
  "statements": [
    {
      "query": "MATCH(:TypeA)-[r:REL]->(:TypeB) WHERE r.lastupdated <> $UPDATE_TAG WITH r LIMIT $LIMIT_SIZE DELETE r",
      "iterative": true,
      "iterationsize": 100
    },{
      "query": "MATCH (n:TypeA) WHERE n.lastupdated <> $UPDATE_TAG WITH n LIMIT $LIMIT_SIZE DETACH DELETE (n)",
      "iterative": true,
      "iterationsize": 100
    },{
      "query": "MATCH (n:TypeB) WHERE n.lastupdated <> $UPDATE_TAG WITH n LIMIT $LIMIT_SIZE DETACH DELETE (n)",
      "iterative": true,
      "iterationsize": 100
    }],
  "name": "cleanup stale resources"
}
"""
