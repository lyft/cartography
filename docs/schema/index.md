# Cartography Schema

### ℹ️ Quick notes on notation
- **Bolded words** in the schema tables indicate that this field is indexed, so your queries will run faster if you use these fields.

- This isn't proper Neo4j syntax, but for the purpose of this document we will use this notation:

	```
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeB, NodeTypeC, NodeTypeD, NodeTypeE)
	```

	to mean a shortened version of this:

	```
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeB)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeC)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeD)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeE)
	```


	In words, this means that `NodeTypeA` has `RELATIONSHIP_R` pointing to `NodeTypeB`, and `NodeTypeA` has `RELATIONSHIP_R` pointing to `NodeTypeC`.

- In these docs, more specific nodes will be decorated with `GenericNode::SpecificNode` notation.  For example, if we have a `Car` node and a `RaceCar` node, we will refer to the `RaceCar` as `Car::RaceCar`.

## Amazon Web Services
- Click [here](aws.md)

## Google Cloud Platform
- Click [here](gcp.md)

## GSuite
- Click [here](gsuite.md)

## CRXcavator Platform
- Click [here](crxcavator.md)

## More to come!
👍
