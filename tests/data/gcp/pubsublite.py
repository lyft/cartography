TEST_SUBSCRIPTIONS = [
    {
        "deliveryConfig": {
            "deliveryRequirement": "DELIVER_IMMEDIATELY",
        },
        "exportConfig": {
            "currentState": "someState",
            "deadLetterTopic": "someTopic",
            "desiredState": "someDesiredState",
            "pubsubConfig": {
                "topic": "projects/project-123/topics/topic2",
            },
        },
        "topic": "projects/project-123/locations/us-central1/topics/topic1",
        "id": "projects/project-123/locations/us-central1/subscriptions/subscription1",
        "name": "subscription1"
    },
    {
        "deliveryConfig": {
            "deliveryRequirement": "DELIVER_IMMEDIATELY",
        },
        "exportConfig": {
            "currentState": "someState",
            "deadLetterTopic": "someTopic",
            "desiredState": "someDesiredState",
            "pubsubConfig": {
                "topic": "projects/project-123/topics/topic1",
            },
        },
        "topic": "projects/project-123/locations/us-central1/topics/topic2",
        "id": "projects/project-123/locations/us-central1/subscriptions/subscription2",
        "name": "subscription2"
    }
]

TEST_TOPICS = [
    {
        "name": "topic1",
        "id": "projects/project-123/locations/us-central1/topics/topic1",
        "partitionConfig": {
            "capacity": {
                "publishMibPerSec": 42,
                "subscribeMibPerSec": 42,
            },
            "count": "1",
            "scale": 42,
        },
        "reservationConfig": {
            "throughputReservation": "projects/project-123/locations/us-central1/reservations/reservation1",
        },
        "retentionConfig": {
            "perPartitionBytes": "512",
            "period": "3600",
        },
    },
    {
        "name": "topic2",
        "id": "projects/project-123/locations/us-central1/topics/topic2",
        "partitionConfig": {
            "capacity": {
                "publishMibPerSec": 42,
                "subscribeMibPerSec": 42,
            },
            "count": "1",
            "scale": 42,
        },
        "reservationConfig": {
            "throughputReservation": "projects/project-123/locations/us-central1/reservations/reservation1",
        },
        "retentionConfig": {
            "perPartitionBytes": "512",
            "period": "3600",
        },
    },
]
