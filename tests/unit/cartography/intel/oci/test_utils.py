from cartography.intel.oci import utils

OCI_OBJECT = """[{
        "capabilities": {
            "can_use_api_keys": true,
            "can_use_auth_tokens": true
        },
        "compartment_id": "ocid1.tenancy.oc1..123"
}]"""

JSON_OCI_OBJECT = {
    "capabilities": {
        "can_use_api_keys": True,
        "can_use_auth_tokens": True,
    },
    "compartment_id": "ocid1.tenancy.oc1..123",
}


def test_oci_object_to_json():
    json_out = utils.oci_object_to_json(OCI_OBJECT)
    assert isinstance(json_out, list)
    assert isinstance(json_out[0]["capabilities"], dict)
    assert isinstance(json_out[0]["compartment-id"], str)
    assert json_out[0]["compartment-id"] == "ocid1.tenancy.oc1..123"


def test_replace_char_in_dict():
    adjusted_dict = utils.replace_char_in_dict(JSON_OCI_OBJECT)
    assert isinstance(adjusted_dict, dict)
    assert "compartment-id" in adjusted_dict.keys()
