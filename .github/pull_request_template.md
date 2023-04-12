
___
Read through our [developer docs](https://lyft.github.io/cartography/dev/developer-guide.html)

If you are modifying or implementing a new intel module
- [ ] Update the [schema](https://github.com/lyft/cartography/tree/master/docs/root/modules)
- [ ] Use our NodeSchema [data model](https://lyft.github.io/cartography/dev/writing-intel-modules.html#defining-a-node)
- [ ] Use specialized functions
  - [ ] `get_` to [fetch](https://lyft.github.io/cartography/dev/writing-intel-modules.html#get) the data
  - [ ] `transform_` do [modifications](https://lyft.github.io/cartography/dev/writing-intel-modules.html#transform) against the data
  - [ ] `load_` begin the database [write](https://lyft.github.io/cartography/dev/writing-intel-modules.html#load) transactions
  - [ ] `cleanup_` to [remove](https://lyft.github.io/cartography/dev/writing-intel-modules.html#cleanup) stale nodes and relationships
- [ ] Add [tests](https://lyft.github.io/cartography/dev/writing-intel-modules.html#making-tests)
  - [ ] Unit tests
    - [ ] Test your `transform_` function with sample data
  - [ ] Integration tests
    - [ ] Use our test [helper functions](https://github.com/lyft/cartography/blob/master/tests/integration/util.py)
    - [ ] Test that the new nodes are created
    - [ ] Check the the new relationships are created
    - [ ] Check that stale nodes will be removed
    - [ ] Check that stale relationships will be removed
