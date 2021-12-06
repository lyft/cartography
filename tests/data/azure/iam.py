DESCRIBE_USERS = [
    {
        "displayName": "contoso1",
        "mail": "'contoso1@gmail.com",
        "mailNickname": "contoso1_gmail.com#EXT#",
        "otherMails": ["contoso1@gmail.com"],
        "proxyAddresses":["SMTP:contoso1@gmail.com"],
        "userPrincipalName":"contoso1_gmail.com#EXT#@microsoft.onmicrosoft.com",
    },
    {
        "displayName": "contoso2",
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
        "securityEnabled": False,
        "theme": None,
        "visibility": "Public",
        "onPremisesProvisioningErrors": [],
    },
    {
        "id": "d7797254-3084-44d0-99c9-a3b5ab149538",
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
        "securityEnabled": False,
        "theme": None,
        "visibility": None,
        "onPremisesProvisioningErrors": [],
    },
]


DESCRIBE_APPLICATIONS = [
    {
        "appId": "00000000-0000-0000-0000-000000000001",
        "identifierUris": ["http://contoso/"],
        "displayName": "My app1",
        "publisherDomain": "contoso.com",
        "signInAudience": "AzureADMyOrg",
    },
    {
        "appId": "00000000-0000-0000-0000-000000000002",
        "identifierUris": ["http://contoso/"],
        "displayName": "My app2",
        "publisherDomain": "contoso.com",
        "signInAudience": "AzureADMyOrg",
    },
]


DESCRIBE_SERVICE_ACCOUNTS = [
    {
        "accountEnabled": True,
        "displayName": "amasf1",
        "servicePrincipalType": "Application",
        "signInAudience": "AzureADMyOrg",
    },
    {
        "accountEnabled": True,
        "displayName": "amasf2",
        "servicePrincipalType": "Application",
        "signInAudience": "AzureADMyOrg",
    },
]

DESCRIBE_DOMAINS = [
    {
        "authenticationType": "authenticationType-value",
        "availabilityStatus": "availabilityStatus-value",
        "isAdminManaged": True,
        "isDefault": True,
        "isInitial": True,
        "isRoot": True,
        "id": "contoso1.com",
        "supportedServices": [
            "Email",
            "OfficeCommunicationsOnline",
        ],
    },
    {
        "authenticationType": "authenticationType-value",
        "availabilityStatus": "availabilityStatus-value",
        "isAdminManaged": True,
        "isDefault": True,
        "isInitial": True,
        "isRoot": True,
        "id": "contoso2.com",
        "supportedServices": [
            "Email",
            "OfficeCommunicationsOnline",
        ],
    },
]
