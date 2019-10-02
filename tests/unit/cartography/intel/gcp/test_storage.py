import cartography.intel.gcp.storage 
from tests.data.gcp.storage import BUCKET_METADATA_RESPONSE
from tests.data.gcp.storage import STORAGE_RESPONSE


def test_get_gcp_bucket_metadata(): 
  '''
  Ensure that get_gcp_bucket_metadata() returns a storage object with the correct fields
  '''
  metadata = cartography.intel.gcp.storage.get_gcp_bucket_metadata(STORAGE_RESPONSE) 
  assert metadata == BUCKET_METADATA_RESPONSE
  assert metadata['id'] == 'bucket_name' 
