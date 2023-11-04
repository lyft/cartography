DESCRIBE_USERS = [
    {
        "id": "user-123",
        "display_name": "contoso1",
        "object_id": "gdvsd43562",
        "mail": "'contoso1@gmail.com",
        "mailNickname": "contoso1_gmail.com#EXT#",
        "otherMails": ["contoso1@gmail.com"],
        "proxyAddresses":["SMTP:contoso1@gmail.com"],
        "userPrincipalName":"contoso1_gmail.com#EXT#@microsoft.onmicrosoft.com",
    },
    {
        "id": "user-321",
        "display_name": "contoso2",
        "object_id": "gdvsd43562we34",
        "mail": "'contoso2@gmail.com",
        "mailNickname": "contoso2_gmail.com#EXT#",
        "otherMails": ["contoso2@gmail.com"],
        "proxyAddresses":["SMTP:contoso2@gmail.com"],
        "userPrincipalName":"contoso2_gmail.com#EXT#@microsoft.onmicrosoft.com",
    },
]

DESCRIBE_GROUPS = [
    {
        "id": "45b7d2e7-b882-4a80-ba97-10b7a63b8fa4",
        "object_id": "45b7d2e7-b882-4a80-ba97-10b7a63b8fa4",
        "deletedDateTime": None,
        "classification": None,
        "createdDateTime": "2018-12-22T02:21:05Z",
        "description": "Self help community for golf",
        "displayName": "Golf Assist",
        "expirationDateTime": None,
        "groupTypes": [
            "Unified",
        ],
        "isAssignableToRole": None,
        "mail": "golfassist@contoso.com",
        "mailEnabled": True,
        "mailNickname": "golfassist",
        "membershipRule": None,
        "membershipRuleProcessingState": None,
        "onPremisesLastSyncDateTime": None,
        "onPremisesSecurityIdentifier": None,
        "onPremisesSyncEnabled": None,
        "preferredDataLocation": "CAN",
        "preferredLanguage": None,
        "proxyAddresses": [
            "smtp:golfassist@contoso.onmicrosoft.com",
            "SMTP:golfassist@contoso.com",
        ],
        "renewedDateTime": "2018-12-22T02:21:05Z",
        "resourceBehaviorOptions": [],
        "resourceProvisioningOptions": [],
        "security_enabled": False,
        "theme": None,
        "visibility": "Public",
        "onPremisesProvisioningErrors": [],
    },
    {
        "id": "d7797254-3084-44d0-99c9-a3b5ab149538",
        "object_id": "d7797254-3084-44d0-99c9-a3b5ab149538",
        "deletedDateTime": None,
        "classification": None,
        "createdDateTime": "2018-11-19T20:29:40Z",
        "description": "Talk about golf",
        "displayName": "Golf Discussion",
        "expirationDateTime": None,
        "groupTypes": [],
        "isAssignableToRole": None,
        "mail": "golftalk@contoso.com",
        "mailEnabled": True,
        "mailNickname": "golftalk",
        "membershipRule": None,
        "membershipRuleProcessingState": None,
        "onPremisesLastSyncDateTime": None,
        "onPremisesSecurityIdentifier": None,
        "onPremisesSyncEnabled": None,
        "preferredDataLocation": "CAN",
        "preferredLanguage": None,
        "proxyAddresses": [
            "smtp:golftalk@contoso.onmicrosoft.com",
            "SMTP:golftalk@contoso.com",
        ],
        "renewedDateTime": "2018-11-19T20:29:40Z",
        "resourceBehaviorOptions": [],
        "resourceProvisioningOptions": [],
        "security_enabled": False,
        "theme": None,
        "visibility": None,
        "onPremisesProvisioningErrors": [],
    },
]


DESCRIBE_APPLICATIONS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "object_id": "00000000-0000-0000-0000-000000000001",
        "identifierUris": ["http://contoso/"],
        "display_name": "My app1",
        "publisher_domain": "contoso.com",
        "sign_in_audience": "AzureADMyOrg",
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "object_id": "00000000-0000-0000-0000-000000000002",
        "identifierUris": ["http://contoso/"],
        "display_name": "My app2",
        "publisher_domain": "contoso.com",
        "sign_in_audience": "AzureADMyOrg",
    },
]


DESCRIBE_SERVICE_ACCOUNTS = [
    {
        "id": "86823hkhjhd",
        "object_id": "86823hkhjhd",
        "account_enabled": True,
        "display_name": "amasf1",
        "service_principal_type": "Application",
        "signInAudience": "AzureADMyOrg",
    },
    {
        "id": "hvhg575757g",
        "object_id": "hvhg575757g",
        "account_enabled": True,
        "display_name": "amasf2",
        "service_principal_type": "Application",
        "signInAudience": "AzureADMyOrg",
    },
]

DESCRIBE_DOMAINS = [
    {
        "id": "contoso1.com",
        "authentication_type": "authenticationType-value",
        "availabilityStatus": "availabilityStatus-value",
        "isAdminManaged": True,
        "isDefault": True,
        "isInitial": True,
        "isRoot": True,
        "name": "contoso1.com",
        "supportedServices": [
            "Email",
            "OfficeCommunicationsOnline",
        ],
    },
    {
        "id": "contoso2.com",
        "authentication_type": "authenticationType-value",
        "availabilityStatus": "availabilityStatus-value",
        "isAdminManaged": True,
        "isDefault": True,
        "isInitial": True,
        "isRoot": True,
        "name": "contoso2.com",
        "supportedServices": [
            "Email",
            "OfficeCommunicationsOnline",
        ],
    },
]

DESCRIBE_ROLES = [
    {
        "id": "97254c67-852d-61c20eb66ffc",
        "name": "852d",
        "type": "Microsoft.Authorization/roleAssignments",
        "roleName": "Owner",
        "permissions": ["*"],
        "principal_id": "86823hkhjhd",
    },
    {
        "id": "97254c67-852d-61c20eb66ffcsdds",
        "name": "852dqqe",
        "type": "Microsoft.Authorization/roleAssignments",
        "roleName": "Owner",
        "permissions": ["*"],
        "principal_id": "hvhg575757g",
    },
]
