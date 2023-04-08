class PropertyRef:
    """
    PropertyRefs represent properties on cartography nodes and relationships. Here is how they are used:

    (1) cartography takes lists of Python dicts and loads them to Neo4j. PropertyRefs allow our dynamically generated
    Neo4j ingestion queries to set values for a given node or relationship property from
        (A) a field on the dict being processed (PropertyRef.set_in_kwargs=False; default), or
        (B) from a single variable provided by a keyword argument (PropertyRef.set_in_kwargs=True).

    (2) PropertyRefs defined on CartographyNodeProperties objects can specify the `extra_index=True` field to ensure
    that an index is created for that given node on the given property.

    (3) When we need to create a relationship from node A to node B based on the value of one or more of node B's
    properties, cartography uses PropertyRefs on TargetNodeMatcher objects to generate an appropriate Neo4j `MATCH`
    clause. This clause may need special handling, such as when we need to match on one of node B's properties in a
    case-insensitive way - see the constructor docs for more details.
    """

    def __init__(self, name: str, set_in_kwargs=False, extra_index=False, ignore_case=False):
        """
        :param name: The name of the property
        :param set_in_kwargs: Optional. This param only has effect if the PropertyRef is part of
        CartographyNodeProperties or CartographyRelProperties objects.
        If True, instructs the querybuilder to find the value for this property name in the kwargs passed to it.
        This is used for things like applying the same update tag to all nodes of a given run.
        If False (default), we instruct the querybuilder to get the value for this given property from
        the current dict being processed.
        :param extra_index: This param only has effect if the PropertyRef is part of a CartographyNodeProperties object.
        If True, make sure that we create an index for this property name.
          Notes:
          - extra_index is available for the case where you anticipate a property will be queried frequently.
          - The `id` and `lastupdated` properties will always have indexes created for them automatically by
            `ensure_indexes()`.
          - All properties included in target node matchers will always have indexes created for them.
            Defaults to False.
        :param ignore_case: This param only has effect as part of a TargetNodeMatcher, and this is not
        supported for the sub resource relationship. If True, performs a case-insensitive match when comparing the value
        of this property during relationship creation. Defaults to False.
            Example on why you would set this to True:
            GitHub usernames can have both uppercase and lowercase characters, but GitHub itself treats usernames as
            case-insensitive. Suppose your company's internal personnel database stores GitHub usernames all as
            lowercase. If you wanted to map your company's employees to their GitHub identities, you would need to
            perform a case-insensitive match between your company's record of a user's GitHub username and your
            cartography catalog of GitHubUser nodes. Therefore, you would need `ignore_case=True` in the PropertyRef
            that points to the GitHubUser node's name field, otherwise if one of your employees' GitHub usernames
            contains capital letters, you would not be able to map them properly to a GitHubUser node in your graph.
        """
        self.name: str = name
        self.set_in_kwargs: bool = set_in_kwargs
        self.extra_index: bool = extra_index
        self.ignore_case: bool = ignore_case

    def _parameterize_name(self) -> str:
        """
        Private function. Turns self.name into a Neo4j query parameter so that the Neo4j ingestion query can access the
        value on the dictionary being processed. This is used when parameters are supplied to the querybuilder via
        kwargs.
        Relevant Neo4j references: https://neo4j.com/docs/python-manual/current/query-simple/#_write_to_the_database and
        https://neo4j.com/docs/cypher-manual/current/syntax/parameters/.
        """
        return f"${self.name}"

    def __repr__(self) -> str:
        """
        Returns string representation of the property so that it can be rendered in the querybuilder based on the
        various inputs passed to the constructor.
        """
        if self.set_in_kwargs:
            return self._parameterize_name()

        if self.name.lower() == 'id' or self.ignore_case:
            # Don't do coalesce() on caseinsensitive attr match.
            return f"item.{self.name}"

        # Attention: This implementation detail is quirky and deserves the following essay to explain.
        # This function ensures that the Neo4j query sets the value of this node/relationship property by checking the
        # following sources in order:
        # 1. the current dict being processed. That is, we check if dict `item` contains a key called `self.name` with
        # a non-None value. If so, we use that value. Else continue and check the next source.
        # 2. An existing value on the node itself. That is, we convert self.name to lowercase and check if that is non
        # null on the Neo4j node `i` already. If None, then the property is not set (this a Neo4j driver behavior).
        # This means we make an ASSUMPTION that the property name set on the node is the lowercase version of self.name.
        #
        # We do this because not all fields defined on a given CartographyNodeSchema may be present on the dict being
        # processed (this is by design because we encourage multiple intel modules to update the same nodes as they
        # may enrich the node with different properties), and when a dict is processed by the Neo4j driver, fields that
        # are not defined on the dict are treated as None values.
        #
        # As an example, the EC2 instance sync loads in :EC2Instances with :EBSVolumes attached based on the output of
        # `describe-ec2-instances`. This data includes a field called `deleteontermination` on the :EBSVolume.
        # `deleteontermination` is only set during the EC2 instance sync. When the EBS Volume sync runs, it enriches
        # existing :EBSVolumes with additional fields from data retrieved with `describe-ebs-volumes` but because this
        # API call does not include `deleteontermination`, we will overwrite the previous values of
        # `deleteontermination` with `None`, thus removing the property from all :EBSVolumes.
        return f"COALESCE(item.{self.name}, i.{self.name.lower()})"
