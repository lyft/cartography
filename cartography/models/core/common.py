class PropertyRef:
    """
    PropertyRefs represent properties on cartography nodes and relationships.

    cartography takes lists of Python dicts and loads them to Neo4j. PropertyRefs allow our dynamically generated Neo4j
    ingestion queries to set values for a given node or relationship property from (A) a field on the dict being
    processed (PropertyRef.set_in_kwargs=False; default), or (B) from a single variable provided by a keyword argument
    (PropertyRef.set_in_kwargs=True).
    """

    def __init__(self, name: str, set_in_kwargs=False):
        """
        :param name: The name of the property
        :param set_in_kwargs: Optional. If True, the property is not defined on the data dict, and we expect to find the
        property in the kwargs.
        If False, looks for the property in the data dict.
        Defaults to False.
        """
        self.name = name
        self.set_in_kwargs = set_in_kwargs

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
        return f"item.{self.name}" if not self.set_in_kwargs else self._parameterize_name()
