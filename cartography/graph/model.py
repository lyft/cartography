import abc
from dataclasses import dataclass
from dataclasses import field
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
    processed (PropertyRef. set_in_kwargs =False, default), or (B) from a single variable provided by a keyword argument
    (PropertyRef. set_in_kwargs =True).
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
        By default, the querybuilder will render an UNWIND query so that
        the value for this property will come from the dict being processed.
        If set_in_kwargs is True, then the value will instead come from kwargs.
        """
        return f"item.{self.name}" if not self.set_in_kwargs else self._parameterize_name()


@dataclass
class CartographyNodeProperties(abc.ABC):
    """
    Abstract base dataclass that represents the properties on a CartographyNodeSchema. This is intended to enforce that
    all subclasses will have an id and a lastupdated field defined on their resulting nodes.
    """
    id: PropertyRef = field(init=False)
    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        """
        Designed to prevent direct instantiation. This workaround is needed since this is both an abstract class and a
        dataclass.
        See https://stackoverflow.com/q/60590442.
        """
        if self.__class__ == CartographyNodeProperties:
            raise TypeError("Cannot instantiate abstract class.")


@dataclass
class CartographyRelProperties(abc.ABC):
    """
    Abstract class that represents the properties on a CartographyRelSchema. This is intended to enforce that all
    subclasses will have a lastupdated field defined on their resulting relationships.
    """
    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        """
        Designed to prevent direct instantiation. This workaround is needed since this is both an abstract class and a
        dataclass.
        """
        if self.__class__ == CartographyRelProperties:
            raise TypeError("Cannot instantiate abstract class.")


@dataclass
class CartographyRelSchema(abc.ABC):
    """
    Abstract base dataclass that represents a cartography relationship.

    The CartographyRelSchema contains properties that make it possible to connect the CartographyNodeSchema to other
    existing nodes in the graph.
    """
    _target_node_key_refs: Dict[str, PropertyRef] = field(init=False)

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
    def target_node_key_refs(self) -> Dict[str, PropertyRef]:
        """
        :return: A dict mapping
        From: one or more attribute names on the target_node_label used to uniquely identify what node to connect to.
        To: The value of the target_node_key used to uniquely identify what node to connect to. This is given as a
        PropertyRef.
        """
        return self._target_node_key_refs

    @target_node_key_refs.setter
    def target_node_key_refs(self, key_refs: Dict[str, PropertyRef]) -> None:
        """
        Boilerplate setter function used to keep typehints happy.
        """
        self._target_node_key_refs = key_refs

    @property
    @abc.abstractmethod
    def rel_label(self) -> str:
        """
        :return: The str label of the relationship.
        """
        pass

    @property
    @abc.abstractmethod
    def direction(self) -> LinkDirection:
        """
        :return: The LinkDirection of the query. Please see the `LinkDirection` docs for a detailed explanation.
        """
        pass


@dataclass
class CartographyNodeSchema(abc.ABC):
    """
    Abstract base dataclass that represents a graph node in cartography. This is used to dynamically generate graph
    ingestion queries.

    A CartographyNodeSchema is composed of:

    - CartographyNodeProperties: contains the properties on the node and where to find their values with PropertyRef
    objects.
    - [Optional] A CartographyRelSchema pointing to the node's sub-resource (see the docstring on
      `sub_resource_relationship` for details.
    - [Optional] One or more other CartographyRelSchemas to other nodes.
    """
    _extra_labels: Optional[List[str]] = field(init=False, default=None)
    _other_relationships: Optional[List[CartographyRelSchema]] = field(init=False, default=None)

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
    def other_relationships(self) -> Optional[List[CartographyRelSchema]]:
        """
        Optional.
        Allows subclasses to specify additional cartography relationships on the node.
        :return: None of not overriden. Else return a list of CartographyRelSchema associated with the node.
        """
        return self._other_relationships

    @other_relationships.setter
    def other_relationships(self, other_rels: List[CartographyRelSchema]) -> None:
        """
        Boilerplate setter function used to keep typehints happy.
        """
        self._other_relationships = other_rels

    @property
    def extra_labels(self) -> Optional[List[str]]:
        """
        Optional.
        Allows specifying extra labels on the node.
        :return: None if not overriden. Else return a str list of the extra labels specified on the node.
        """
        return self._extra_labels

    @extra_labels.setter
    def extra_labels(self, labels: List[str]) -> None:
        """
        Boilerplate setter function used to keep typehints happy.
        """
        self._extra_labels = labels
