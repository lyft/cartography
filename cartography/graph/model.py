import abc
from dataclasses import dataclass
from dataclasses import field
from enum import auto
from enum import Enum
from typing import List
from typing import Optional


class LinkDirection(Enum):
    """
    If a CartographyNodeSchema has relationships, then it will have one or more CartographyRelSchemas.

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
    We dynamically build Neo4j queries and allow module authors to define a schema for their nodes and relationships.

    The end result is we write dicts to Neo4j. To define nodes and rels, we need a mechanism to allow the schema to
    refer to properties on the data dict.

    A PropertyRef is how we reference properties on the data dict when dynamically creating queries.
    """

    def __init__(self, name: str, static=False):
        """
        :param name: The name of the property as seen on the data dict
        :param static: If true, the property is not defined on the data dict, and we expect to find the property in the
        kwargs.
        If False, looks for the property in the data dict.
        Defaults to False.
        """
        self.name = name
        # TODO consider naming this something better
        self.static = static

    def _parameterize_name(self) -> str:
        return f"${self.name}"

    def __repr__(self) -> str:
        return f"item.{self.name}" if not self.static else self._parameterize_name()


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

    A CartographyNodeSchema is composed of a CartographyRelSchema. The CartographyRelSchema contains properties that
    make it possible to connect the CartographyNodeSchema to other existing nodes in the graph.

    As example usage, this code:

        class EMRCluster(CartographyNodeSchema):
            label: str = "EMRCluster"
            properties: EMRClusterNodeProperties = EMRClusterNodeProperties()
            sub_resource_relationship: CartographyRelSchema = EMRClusterToAWSAccount()

        class EMRClusterToAWSAccount(CartographyRelSchema):
            target_node_label: str = 'AWSAccount'
            target_node_key: str = 'id'
            direction: LinkDirection = LinkDirection.INWARD
            rel_label: str = "RESOURCE"
            properties: EMRClusterToAwsAccountRelProperties = EMRClusterToAwsAccountRelProperties()
            target_node_key_property_ref: PropertyRef = PropertyRef('AccountId', static=True)


    generates a Neo4j query that looks like this:

        UNWIND $DictList AS item
            MERGE (i:EMRCluster{id: <... Expand the EMRClusterNodeProperties here ...>})
            ON CREATE SET i.firstseen = timestamp()
            SET
                // ... Expand EMRClusterNodeProperties here ...

            WITH i, item
            MATCH (j:AWSAccount{id: $AccountId})
            MERGE (i)<-[r:RESOURCE]-(j)
            ON CREATE SET r.firstseen = timestamp()
            SET
                // ... Expand EMRClusterToAwsAccountRelProperties here ...
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
    def target_node_key(self) -> str:
        """
        :return: The attribute on the target node used to uniquely identify what node to connect to.
        """
        pass

    @property
    @abc.abstractmethod
    def target_node_key_property_ref(self) -> PropertyRef:
        """
        :return: The value of the target node attribute used to uniquely identify what node to connect to.
        This is given as a PropertyRef.
        """
        pass

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
