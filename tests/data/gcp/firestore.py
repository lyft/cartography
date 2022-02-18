FIRESTORE_DATABASES = [
    {
        'name': 'firestoredatabase123',
        'id': 'firestoredatabase123',
        'locationId': 'location123',
        'type': 'FIRESTORE_NATIVE',
        'concurrencyMode': 'OPTIMISTIC',
    },
    {
        'name': 'firestoredatabase456',
        'id': 'firestoredatabase456',
        'locationId': 'location456',
        'type': 'FIRESTORE_NATIVE',
        'concurrencyMode': 'OPTIMISTIC',
    },
]


FIRESTORE_INDEXES = [
    {
        'name': 'index123',
        'id': 'index123',
        'database_id': 'firestoredatabase123',
        'queryScope': 'COLLECTION_GROUP',
        'state': 'READY',
        'composite_index_id': 'abcdefg123',
    },
    {
        'name': 'index456',
        'id': 'index456',
        'database_id': 'firestoredatabase456',
        'queryScope': 'COLLECTION_GROUP',
        'state': 'READY',
        'composite_index_id': 'abcdefg456',
    },
]
