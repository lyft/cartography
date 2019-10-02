# flake8: noqa
STORAGE_RESPONSE = {
 "kind": "storage#buckets",
 "items": [
  {
   "kind": "storage#bucket",
   "id": "bucket_name",
   "selfLink": "https://www.googleapis.com/storage/v1/b/bucket_name",
   "projectNumber": "some_num",
   "name": "bucket_name",
   "timeCreated": "some_time",
   "updated": "some_time",
   "metageneration": "1",
   "iamConfiguration": {
    "bucketPolicyOnly": {
     "enabled": false
    },
    "uniformBucketLevelAccess": {
     "enabled": false
    }
   },
   "location": "US",
   "locationType": "multi-region",
   "defaultEventBasedHold": false,
   "storageClass": "STANDARD",
   "etag": "CAE="
  }
 ]
}

BUCKET_METADATA_RESPONSE = {
 "kind": "storage#bucket",
 "id": "bucket_name",
 "selfLink": "https://www.googleapis.com/storage/v1/b/bucket_name",
 "projectNumber": "some_num",
 "name": "bucket_name",
 "timeCreated": "some_time",
 "updated": "some_time",
 "metageneration": "1",
 "iamConfiguration": {
  "bucketPolicyOnly": {
   "enabled": false
  },
  "uniformBucketLevelAccess": {
   "enabled": false
  }
 },
 "location": "US",
 "locationType": "multi-region",
 "defaultEventBasedHold": false,
 "storageClass": "STANDARD",
 "etag": "CAE="
}

