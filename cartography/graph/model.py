import abc
from dataclasses import dataclass
from dataclasses import field
from dataclasses import make_dataclass
from enum import auto
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional


class LinkDirection(Enum):
    """
    Each CartographyRelSchema has a LinkDirection that determines whether the relationship points toward the original
    node ("INWARD") or away from the original node ("OUTWARD").

    For example the following code creates the path `(:EMRCluster)<-[:RESOURCE]-(:AWSAccount)`:

        class EMRCluster(CartographyNodeSchema):
            label: str = "EMRCluster"
            sub_resource_relationship: CartographyRelSchema = EMRClusterToAWSAccount()
            # ...

        class EMRClusterToAWSAccount(CartographyRelSchema):
            target_node_label: str = "AWSAccount"
            rel_label: str = "RESOURCE"
            direction: LinkDirection = LinkDirection.INWARD
            # ...

    If `EMRClusterToAWSAccount.direction` was LinkDirection.OUTWARD, then the directionality of the relationship would
    be `(:EMRCluster)-[:RESOURCE]->(:AWSAccount)` instead.
    """
    INWARD = auto()
    OUTWARD = auto()


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


@dataclass(frozen=True)
class CartographyNodeProperties(abc.ABC):
    """
    Abstract base dataclass that represents the properties on a CartographyNodeSchema. This class is abstract so that we
    can enforce that all subclasses have an id and a lastupdated field. These fields are assigned to the node in the
    `SET` clause.
    """
    id: PropertyRef = field(init=False)
    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        """
        Data validation.
        1. Prevents direct instantiation. This workaround is needed since this is a dataclass and an abstract
        class without an abstract method defined. See https://stackoverflow.com/q/60590442.
        2. Stops reserved words from being used as attribute names. See https://github.com/lyft/cartography/issues/1064.
        """
        if self.__class__ == CartographyNodeProperties:
            raise TypeError("Cannot instantiate abstract class.")

        if hasattr(self, 'firstseen'):
            raise TypeError(
                "`firstseen` is a reserved word and is automatically set by the querybuilder on cartography nodes, so "
                f'it cannot be used on class "{type(self).__name__}(CartographyNodeProperties)". Please either choose '
                "a different name for `firstseen` or omit altogether.",
            )


@dataclass(frozen=True)
class CartographyRelProperties(abc.ABC):
    """
    Abstract class that represents the properties on a CartographyRelSchema. This is intended to enforce that all
    subclasses will have a lastupdated field defined on their resulting relationships. These fields are assigned to the
    relationship in the `SET` clause.
    """
    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        """
        Data validation.
        1. Prevents direct instantiation. This workaround is needed since this is a dataclass and an abstract
        class without an abstract method defined. See https://stackoverflow.com/q/60590442.
        2. Stops reserved words from being used as attribute names. See https://github.com/lyft/cartography/issues/1064.
        """
        if self.__class__ == CartographyRelProperties:
            raise TypeError("Cannot instantiate abstract class.")

        if hasattr(self, 'firstseen'):
            raise TypeError(
                "`firstseen` is a reserved word and is automatically set by the querybuilder on cartography rels, so "
                f'it cannot be used on class "{type(self).__name__}(CartographyRelProperties)". Please either choose '
                "a different name for `firstseen` or omit altogether.",
            )


@dataclass(frozen=True)
class TargetNodeMatcher:
    """
    Dataclass used to encapsulate the following mapping:
    Keys: one or more attribute names on the target_node_label used to uniquely identify what node to connect to.
    Values: The value of the target_node_key used to uniquely identify what node to connect to. This is given as a
    PropertyRef.
    This is used to ensure dataclass immutability when composed as part of a CartographyNodeSchema object.
    See `make_target_node_matcher()`.
    """
    pass


@dataclass(frozen=True)
class CartographyRelSchema(abc.ABC):
    """
    Abstract base dataclass that represents a cartography relationship.

    The CartographyRelSchema contains properties that make it possible to connect the CartographyNodeSchema to other
    existing nodes in the graph.
    """
    @property
    @abc.abstractmethod
    def properties(self) -> CartographyRelProperties:
        """
        :return: The properties of the relationship.
        """
        pass

    @property
    @abc.abstractmethod
    def target_node_label(self) -> str:
        """
        :return: The target node label that this relationship will connect to.
        """
        pass

    @property
    @abc.abstractmethod
    def target_node_matcher(self) -> TargetNodeMatcher:
        """
        :return: A TargetNodeMatcher object used to find what node(s) to attach the relationship to.
        """
        pass

    @property
    @abc.abstractmethod
    def rel_label(self) -> str:
        """
        :return: The string label of the relationship.
        """
        pass

    @property
    @abc.abstractmethod
    def direction(self) -> LinkDirection:
        """
        :return: The LinkDirection of the query. Please see the `LinkDirection` docs for a detailed explanation.
        """
        pass


@dataclass(frozen=True)
class OtherRelationships:
    """
    Encapsulates a list of CartographyRelSchema. This is used to ensure dataclass immutability when composed as part of
    a CartographyNodeSchema object.
    """
    rels: List[CartographyRelSchema]


@dataclass(frozen=True)
class ExtraNodeLabels:
    """
    Encapsulates a list of str representing additional labels for the CartographyNodeSchema that this is composed on.
    This wrapping is used to ensure dataclass immutability for the CartographyNodeSchema.
    """
    labels: List[str]


@dataclass(frozen=True)
class CartographyNodeSchema(abc.ABC):
    """
    Abstract base dataclass that represents a graph node in cartography. This is used to dynamically generate graph
    ingestion queries.
    """
    @property
    @abc.abstractmethod
    def label(self) -> str:
        """
        :return: The primary str label of the node.
        """
        pass

    @property
    @abc.abstractmethod
    def properties(self) -> CartographyNodeProperties:
        """
        :return: The properties of the node.
        """
        pass

    @property
    def sub_resource_relationship(self) -> Optional[CartographyRelSchema]:
        """
        Optional.
        Allows subclasses to specify a subresource relationship for the given node. "Sub resource" is a term we made up
        best defined by examples:
        - In the AWS module, the subresource is an AWSAccount
        - In Azure, the subresource is a Subscription
        - In GCP, the subresource is a GCPProject
        - In Okta, the subresource is an OktaOrganization
        ... and so on and so forth.
        :return:
        """
        return None

    @property
    def other_relationships(self) -> Optional[OtherRelationships]:
        """
        Optional.
        Allows subclasses to specify additional cartography relationships on the node.
        :return: None if not overriden. Else return the node's OtherRelationships.
        """
        return None

    @property
    def extra_node_labels(self) -> Optional[ExtraNodeLabels]:
        """
        Optional.
        Allows specifying extra labels on the node.
        :return: None if not overriden. Else return the ExtraNodeLabels specified on the node.
        """
        return None


def make_target_node_matcher(key_ref_dict: Dict[str, PropertyRef]) -> TargetNodeMatcher:
    """
    :param key_ref_dict: A Dict mapping keys present on the node to PropertyRef objects.
    :return: A TargetNodeMatcher used for CartographyRelSchema to match with other nodes.
    """
    fields = [(key, PropertyRef, field(default=prop_ref)) for key, prop_ref in key_ref_dict.items()]
    return make_dataclass(TargetNodeMatcher.__name__, fields, frozen=True)()
