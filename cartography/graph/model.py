import abc
from dataclasses import dataclass
from dataclasses import field
from enum import auto
from enum import Enum
from typing import List
from typing import Optional


class LinkDirection(Enum):
    OUTWARD = auto()
    INWARD = auto()


class PropertyRef:
    """
    We dynamically build Neo4j queries and allow module authors to define a schema for their
    nodes and relationships.

    The end result is we write dicts to Neo4j. To define nodes and rels, we need a mechanism
    to allow the schema to refer to properties on the data dict.

    A PropertyRef is how we reference properties on the data dict when dynamically creating
    queries.
    """

    def __init__(self, name: str, static=False):
        # The name of the property as seen on the data dict
        self.name = name
        # If true, the property is not defined on the data dict. Otherwise look for the property
        # in the data dict.
        # TODO consider naming this something better
        self.static = static

    def _parameterize_name(self) -> str:
        return f"${self.name}"

    def __repr__(self) -> str:
        return f"item.{self.name}" if not self.static else self._parameterize_name()


@dataclass
class CartographyNodeProperties(abc.ABC):
    # Enforce that all subclasses will have an id and a lastupdated field
    id: PropertyRef = field(init=False)
    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        if self.__class__ == CartographyNodeProperties:
            raise TypeError("Cannot instantiate abstract class.")


@dataclass
class CartographyRelProperties(abc.ABC):
    lastupdated: PropertyRef = field(init=False)


@dataclass
class CartographyRelSchema(abc.ABC):
    @property
    @abc.abstractmethod
    def properties(self) -> CartographyRelProperties:
        pass

    @property
    @abc.abstractmethod
    def target_node_label(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def target_node_key(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def rel_label(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def direction(self) -> LinkDirection:
        pass

    @property
    @abc.abstractmethod
    # TODO name this something better maybe
    def dict_field_ref(self) -> PropertyRef:
        pass


@dataclass
class CartographyNodeSchema(abc.ABC):
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
    def subresource_relationship(self) -> Optional[CartographyRelSchema]:
        """
        Optional.
        Allows subclasses to specify a subresource relationship for the given node. "Subresource" is a term we made up
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
        self._other_relationships = other_rels

    @property
    def extra_labels(self) -> Optional[List[str]]:
        """
        Optional.
        Allows subclasses to specify extra labels on the node.
        :return: None if not overriden. Else return a str list of the extra labels specified on the node.
        """
        return self._extra_labels

    @extra_labels.setter
    def extra_labels(self, labels: List[str]) -> None:
        self._extra_labels = labels
