import cartography.intel.gcp.storage 
from tests.data.gcp.storage import STORAGE_RESPONSE


def test_transform_gcp_buckets(): 
  '''
  Ensure that transform_gcp_buckets() returns a list of buckets with the correct fields. 
  '''
  bucket_list = cartography.intel.gcp.storage.transform_gcp_buckets(STORAGE_RESPONSE) 
  assert len(bucket_list) == 1
  
  bucket = bucket_list[0]
  assert len(bucket['items']) == 1 
  assert bucket['type'] == 'storage#buckets' 
  assert bucket['items'][0]['id'] == 'bucket_name' 
  assert bucket['items'][0]['selfLink'] == 'https://www.googleapis.com/storage/v1/b/bucket_name'
  assert bucket['items'][0]['iamConfiguration']['uniformBucketLevelAccess']['enabled'] == False
