class PropertyRef:
    """
    PropertyRefs represent properties on cartography nodes and relationships.

    cartography takes lists of Python dicts and loads them to Neo4j. PropertyRefs allow our dynamically generated Neo4j
    ingestion queries to set values for a given node or relationship property from (A) a field on the dict being
    processed (PropertyRef.set_in_kwargs=False; default), or (B) from a single variable provided by a keyword argument
    (PropertyRef.set_in_kwargs=True).
    """

    def __init__(self, name: str, set_in_kwargs=False, extra_index=False, ignore_case=False):
        """
        :param name: The name of the property
        :param set_in_kwargs: Optional. If True, the property is not defined on the data dict, and we expect to find the
        property in the kwargs.
        If False, looks for the property in the data dict.
        Defaults to False.
        :param extra_index: If True, make sure that we create an index for this property name.
          Notes:
          - extra_index is available for the case where you anticipate a property will be queried frequently.
          - The `id` and `lastupdated` properties will always have indexes created for them automatically by
            `ensure_indexes()`.
          - All properties included in target node matchers will always have indexes created for them.
            Defaults to False.
        :param ignore_case: If True, performs a case-insensitive match when comparing the value of this property during
        relationship creation. Defaults to False. This only has effect as part of a TargetNodeMatcher, and this is not
        supported for the sub resource relationship.
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
        return f"${self.name}"

    def __repr__(self) -> str:
        """
        `querybuilder.build_ingestion_query()`, generates a Neo4j batched ingestion query of the form
        `UNWIND $DictList AS item [...]`.

        If set_in_kwargs is False (default), we instruct the querybuilder to get the value for this given property from
        the dict being processed. To do this, this function returns "item.<key on the dict>". This is used for loading
        in lists of nodes.

        On the other hand if set_in_kwargs is True, then the value will instead come from kwargs passed to
        querybuilder.build_ingestion_query(). This is used for things like applying the same update tag to all nodes of
        a given run.
        """
        if self.set_in_kwargs:
            return self._parameterize_name()
        if self.name.lower() == 'id' or self.ignore_case:  # Don't do coalesce() on caseinsensitive attr match.
            return f"item.{self.name}"
        # TODO add doc on why we do the self.name.lower() and the assumed convention of lowercase for the node
        return f"COALESCE(item.{self.name}, i.{self.name.lower()})"
