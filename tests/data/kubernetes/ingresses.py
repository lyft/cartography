from uuid import uuid4

from tests.data.kubernetes.namespaces import GET_CLUSTER_DATA
from tests.data.kubernetes.namespaces import GET_NAMESPACES_DATA
from tests.data.kubernetes.services import GET_SERVICES_DATA


GET_INGRESSES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-ingress",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": GET_NAMESPACES_DATA[-1]["name"],
        "cluster_uid": GET_CLUSTER_DATA["uid"],
        "rules": [
            {
                "host": "my-host",
                "http_paths": [
                    {
                        "path": "/admin",
                        "path_type": "Prefix",
                        "service": GET_SERVICES_DATA[-1]["name"],
                        "port": 80,
                    },
                ],
            },
        ],
    },
]
