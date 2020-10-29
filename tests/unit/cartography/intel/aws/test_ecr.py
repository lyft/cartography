from cartography.intel.aws import ecr
from tests.data.aws.ecr import GET_ECR_REPOSITORY_IMAGE_VULNS


def test_transform_repository_image_vulns():
    transformed_data = ecr.transform_ecr_repository_image_vulns(GET_ECR_REPOSITORY_IMAGE_VULNS)
    assert transformed_data['findings'][0]['package_name'] == 'some_name'
    assert transformed_data['findings'][0]['package_version'] == '1.2.3'
