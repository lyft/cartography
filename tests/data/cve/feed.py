GET_CVE_SYNC_METADATA = {
    "CVE_data_type": "CVE",
    "CVE_data_format": "MITRE",
    "CVE_data_version": "4.0",
    "CVE_data_numberOfCVEs": "6769",
    "CVE_data_timestamp": "2022-02-23T08:01Z",
    "CVE_Items": [{
        "cve": {
            "data_type": "CVE",
            "data_format": "MITRE",
            "data_version": "4.0",
            "CVE_data_meta": {
                "ID": "CVE-1999-0001",
                "ASSIGNER": "cve@mitre.org",
            },
            "problemtype": {
                "problemtype_data": [{
                    "description": [{
                        "lang": "en",
                        "value": "CWE-20",
                    }],
                }],
            },
            "references": {
                "reference_data": [
                    {
                        "url": "http://www.openbsd.org/errata23.html#tcpfix",
                        "name": "http://www.openbsd.org/errata23.html#tcpfix",
                        "refsource": "CONFIRM",
                        "tags": [],
                    }, {
                        "url": "http://www.osvdb.org/5707",
                        "name": "5707",
                        "refsource": "OSVDB",
                        "tags": [],
                    },
                ],
            },
            "description": {
                "description_data": [{
                    "lang": "en",
                    "value": (
                        "ip_input.c in BSD-derived TCP/IP implementations allows remote "
                        "attackers to cause a denial of service (crash or hang) via "
                        "crafted packets."
                    ),
                }],
            },
        },
        "configurations": {
            "CVE_data_version": "4.0",
            "nodes": [{
                "operator": "OR",
                "children": [],
                "cpe_match": [
                    {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:1.0:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:1.1.5.1:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.1.7:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.2:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.2.8:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:openbsd:openbsd:2.3:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:bsdi:bsd_os:3.1:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.2.3:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.2.4:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.2.5:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.2.6:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.0:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.0.5:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.1.5:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.1.6:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.2.2:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.0.1:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:1.1:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:1.2:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.1.6.1:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:2.1.7.1:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:freebsd:freebsd:3.0:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    }, {
                        "vulnerable": True,
                        "cpe23Uri": "cpe:2.3:o:openbsd:openbsd:2.4:*:*:*:*:*:*:*",
                        "cpe_name": [],
                    },
                ],
            }],
        },
        "impact": {
            "baseMetricV2": {
                "cvssV2": {
                    "version": "2.0",
                    "vectorString": "AV:N/AC:L/Au:N/C:N/I:N/A:P",
                    "accessVector": "NETWORK",
                    "accessComplexity": "LOW",
                    "authentication": "NONE",
                    "confidentialityImpact": "NONE",
                    "integrityImpact": "NONE",
                    "availabilityImpact": "PARTIAL",
                    "baseScore": 5.0,
                },
                "severity": "MEDIUM",
                "exploitabilityScore": 10.0,
                "impactScore": 2.9,
                "obtainAllPrivilege": False,
                "obtainUserPrivilege": False,
                "obtainOtherPrivilege": False,
                "userInteractionRequired": False,
            },
        },
        "publishedDate": "1999-12-30T05:00Z",
        "lastModifiedDate": "2010-12-16T05:00Z",
    }],
}
