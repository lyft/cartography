from okta.models.usergroup.UserGroup import UserGroup
from okta.models.usergroup.UserGroupProfile import UserGroupProfile

LIST_GROUP_MEMBER_RESPONSE = """
[
  {
    "id": "00u1f96ECLNVOKVMUSEA",
    "status": "ACTIVE",
    "created": "2013-12-12T16:14:22.000Z",
    "activated": "2013-12-12T16:14:22.000Z",
    "statusChanged": "2013-12-12T22:14:22.000Z",
    "lastLogin": "2013-12-12T22:14:22.000Z",
    "lastUpdated": "2015-11-15T19:23:32.000Z",
    "passwordChanged": "2013-12-12T22:14:22.000Z",
    "profile": {
      "firstName": "Easy",
      "lastName": "E",
      "email": "easy-e@example.com",
      "login": "easy-e@example.com",
      "mobilePhone": null
    },
    "credentials": {
      "password": {},
      "provider": {
        "type": "OKTA",
        "name": "OKTA"
      }
    },
    "_links": {
      "self": {
        "href": "https://{yourOktaDomain}/api/v1/users/00u1f96ECLNVOKVMUSEA"
      }
    }
  },
  {
    "id": "00u1f9cMYQZFMPVXIDIZ",
    "status": "ACTIVE",
    "created": "2013-12-12T16:14:42.000Z",
    "activated": "2013-12-12T16:14:42.000Z",
    "statusChanged": "2013-12-12T16:14:42.000Z",
    "lastLogin": "2013-12-12T18:14:42.000Z",
    "lastUpdated": "2013-12-12T16:14:42.000Z",
    "passwordChanged": "2013-12-12T16:14:42.000Z",
    "profile": {
      "firstName": "Dr.",
      "lastName": "Dre",
      "email": "dr.dre@example.com",
      "login": "dr.dre@example.com",
      "mobilePhone": null
    },
    "credentials": {
      "password": {},
      "provider": {
        "type": "OKTA",
        "name": "OKTA"
      }
    },
    "_links": {
      "self": {
        "href": "https://{yourOktaDomain}/api/v1/users/00u1f9cMYQZFMPVXIDIZ"
      }
    }
  }
]
"""


def create_test_group():
    group = UserGroup()
    group.id = "group_id_value"

    group.profile = UserGroupProfile()
    group.profile.name = "group_profile_name_value"
    group.profile.description = "group_profile_description_value"
    group.profile.samAccountName = "group_profile_samAccountName_value"
    group.profile.dn = "group_profile_dn_value"
    group.profile.windowsDomainQualifiedName = "group_profile_windowsDomainQualifiedName_value"
    group.profile.externalId = "group_profile_external_id_value"

    return group
