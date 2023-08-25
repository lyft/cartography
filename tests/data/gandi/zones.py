GANDI_DNS_ZONES = [
    {
        "fqdn": "lyft.com",
        "tld": "com",
        "status": [
            "clientTransferProhibited",
        ],
        "dates": {
            "created_at": "2020-12-29T18:09:16Z",
            "deletes_at": "2024-02-12T07:09:16Z",
            "hold_begins_at": "2023-12-29T17:09:16Z",
            "hold_ends_at": "2024-02-12T17:09:16Z",
            "pending_delete_ends_at": "2024-03-18T17:09:16Z",
            "registry_created_at": "2020-12-29T17:09:16Z",
            "registry_ends_at": "2023-12-29T17:09:16Z",
            "renew_begins_at": "2012-01-01T00:00:00Z",
            "restore_ends_at": "2024-03-13T17:09:16Z",
            "updated_at": "2023-05-19T13:26:38Z",
            "authinfo_expires_at": "2024-05-18T13:26:38Z",
        },
        "can_tld_lock": True,
        "authinfo": "********",
        "nameservers": [
            "ns-41-a.gandi.net",
            "ns-135-b.gandi.net",
            "ns-138-c.gandi.net",
        ],
        "tags": [],
        "services": [
            "dnssec",
            "gandilivedns",
            "mailboxv2",
        ],
        "autorenew": {
            "duration": 1,
            "dates": [
                "2023-11-28T16:09:16Z",
                "2023-12-14T17:09:16Z",
                "2023-12-28T17:09:16Z",
            ],
            "org_id": "1aeab22b-1c3e-4829-a64f-a51d52014073",
            "href": "https://api.gandi.net/v5/domain/domains/lyft.com/autorenew",
            "enabled": True,
        },
        "contacts": {
            "owner": {},
            "admin": {},
            "tech": {},
            "bill": {},
        },
        "id": "3c31bfaa-3ba9-4f10-b468-404762ffa6a0",
        "sharing_space": {
            "id": "1aeab22b-1c3e-4829-a64f-a51d52014073",
            "name": "LyftOSS",
            "type": "organization",
            "reseller": False,
        },
        "href": "https://api.gandi.net/v5/domain/domains/lyft.com",
        "reachability": "done",
        "fqdn_unicode": "lyft.com",
        "records": [
            {
                "rrset_name": "@",
                "rrset_type": "A",
                "rrset_ttl": 10800,
                "rrset_values": [
                    "1.1.1.1",
                ],
                "rrset_href": "https://api.gandi.net/v5/livedns/domains/lyft.com/records/%40/A",
            },
            {
                "rrset_name": "@",
                "rrset_type": "TXT",
                "rrset_ttl": 10800,
                "rrset_values": [
                    "\"v=spf1 include:spf.mailjet.com ?all\"",
                ],
                "rrset_href": "https://api.gandi.net/v5/livedns/domains/lyft.com/records/%40/TXT",
            },
            {
                "rrset_name": "_DMARC",
                "rrset_type": "CNAME",
                "rrset_ttl": 10800,
                "rrset_values": [
                    "v=DMARC1;p=reject;pct=100;rua=mailto:postmaster@lyft.com",
                ],
                "rrset_href": "https://api.gandi.net/v5/livedns/domains/lyft.com/records/_DMARC/CNAME",
            },
        ],
    },
]
