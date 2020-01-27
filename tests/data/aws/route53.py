NS_RECORD = {
    "Name": "testdomain.net.",
    "Type": "NS",
    "TTL": 172800,
    "ResourceRecords": [
        {"Value": "ns-856.awsdns-43.net"},
        {"Value": "ns-1418.awsdns-49.org."},
        {"Value": "ns-1913.awsdns-47.co.uk."},
        {"Value": "ns-192.awsdns-24.com."},
    ],
}

CNAME_RECORD = {
    "Name": "subdomain.lyft.com.",
    "Type": "CNAME",
    "SetIdentifier": "ca",
    "GeoLocation": {
        "CountryCode": "US",
        "SubdivisionCode": "CA",
    },
    "AliasTarget": {
        "HostedZoneId": "FAKEZONEID",
        "DNSName": "fakeelb.elb.us-east-1.amazonaws.com.",
        "EvaluateTargetHealth": False,
    },
}

ZONE_RECORDS = [
    {
        "Id": "/hostedzone/FAKEZONEID1",
        "Name": "test.com.",
        "CallerReference": "BD057866-DA11-69AA-AE7C-339CDB669D49",
        "Config": {
            "PrivateZone": False,
        },
        "ResourceRecordSetCount": 8,
    },
    {
        "Id": "/hostedzone/FAKEZONEID2",
        "Name": "test.com.",
        "CallerReference": "BD057866-DA11-69AA-AE7C-339CDB669D49",
        "Config": {
            "PrivateZone": False,
        },
        "ResourceRecordSetCount": 8,
    },
]
