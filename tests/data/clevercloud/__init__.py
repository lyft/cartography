CLEVERCLOUD_ORGANISATION = {
  "id": "orga_f3b3bb57-db31-4dff-8708-0dd91cc31826",
  "name": "Dummy",
  "description": "Dummy Corp",
  "billingEmail": "invoices@domain.tld",
  "address": "404, avenue Nowere",
  "city": "Paris",
  "zipcode": "75000",
  "country": "FRANCE",
  "company": "Dummy",
  "VAT": "FR12345678911",
  "avatar": "https://ccapiavatars.cellar-c2.services.clever-cloud.com/orga_f3b3bb57-db31-4dff-8708-0dd91cc31826/avatar.png",
  "vatState": "VALID",
  "customerFullName": "John Doe",
  "canPay": True,
  "cleverEnterprise": False,
  "emergencyNumber": None,
  "canSEPA": True,
  "isTrusted": False
}

CLEVERCLOUD_USERS = [
    {
  "member": {
    "id": "user_8f0c3cb0-c096-4f7e-a249-aa46c24a5941",
    "email": "john.doe@domain.tld",
    "name": "John Doe",
    "avatar": "https://avatars.githubusercontent.com/u/12345?v=4",
    "preferredMFA": "TOTP"
  },
  "role": "ADMIN",
  "job": "Cybersecurity Manager"
}
]


CLEVERCLOUD_APPS = [
  {
  "id": "app_6cb7fded-72d8-4994-b813-c7caa2208019",
  "name": "dummy-api-production",
  "description": "dummy-api-production",
  "zone": "par",
  "instance": {
    "type": "java",
    "version": "20221027",
    "variant": {
      "id": "5163834d-b343-4006-bfdb-ece9d30fbb51",
      "slug": "gradle",
      "name": "Java or Groovy + Gradle",
      "deployType": "java",
      "logo": "https://assets.clever-cloud.com/logos/gradle.svg"
    },
    "minInstances": 2,
    "maxInstances": 2,
    "maxAllowedInstances": 40,
    "minFlavor": {
      "name": "XS",
      "mem": 1024,
      "cpus": 1,
      "gpus": 0,
      "disk": 0,
      "price": 0.3436,
      "available": True,
      "microservice": False,
      "machine_learning": False,
      "nice": 0,
      "price_id": "apps.XS",
      "memory": {
        "unit": "B",
        "value": 1073741824,
        "formatted": "1024 MiB"
      }
    },
    "maxFlavor": {
      "name": "XS",
      "mem": 1024,
      "cpus": 1,
      "gpus": 0,
      "disk": 0,
      "price": 0.3436,
      "available": True,
      "microservice": False,
      "machine_learning": False,
      "nice": 0,
      "price_id": "apps.XS",
      "memory": {
        "unit": "B",
        "value": 1073741824,
        "formatted": "1024 MiB"
      }
    },
    "flavors": [
      {
        "name": "pico",
        "mem": 256,
        "cpus": 1,
        "gpus": 0,
        "disk": 0,
        "price": 0.1073883162,
        "available": True,
        "microservice": True,
        "machine_learning": False,
        "nice": 5,
        "price_id": "apps.pico",
        "memory": {
          "unit": "B",
          "value": 268435456,
          "formatted": "256 MiB"
        }
      },
      {
        "name": "nano",
        "mem": 512,
        "cpus": 1,
        "gpus": 0,
        "disk": 0,
        "price": 0.1431844215,
        "available": True,
        "microservice": True,
        "machine_learning": False,
        "nice": 5,
        "price_id": "apps.nano",
        "memory": {
          "unit": "B",
          "value": 536870912,
          "formatted": "512 MiB"
        }
      },
      {
        "name": "XS",
        "mem": 1024,
        "cpus": 1,
        "gpus": 0,
        "disk": 0,
        "price": 0.3436,
        "available": True,
        "microservice": False,
        "machine_learning": False,
        "nice": 0,
        "price_id": "apps.XS",
        "memory": {
          "unit": "B",
          "value": 1073741824,
          "formatted": "1024 MiB"
        }
      },
      {
        "name": "S",
        "mem": 2048,
        "cpus": 2,
        "gpus": 0,
        "disk": 0,
        "price": 0.6873,
        "available": True,
        "microservice": False,
        "machine_learning": False,
        "nice": 0,
        "price_id": "apps.S",
        "memory": {
          "unit": "B",
          "value": 2147483648,
          "formatted": "2048 MiB"
        }
      },
      {
        "name": "M",
        "mem": 4096,
        "cpus": 4,
        "gpus": 0,
        "disk": 0,
        "price": 1.7182,
        "available": True,
        "microservice": False,
        "machine_learning": False,
        "nice": 0,
        "price_id": "apps.M",
        "memory": {
          "unit": "B",
          "value": 4294967296,
          "formatted": "4096 MiB"
        }
      },
      {
        "name": "L",
        "mem": 8192,
        "cpus": 6,
        "gpus": 0,
        "disk": 0,
        "price": 3.4364,
        "available": True,
        "microservice": False,
        "machine_learning": False,
        "nice": 0,
        "price_id": "apps.L",
        "memory": {
          "unit": "B",
          "value": 8589934592,
          "formatted": "8192 MiB"
        }
      },
      {
        "name": "XL",
        "mem": 16384,
        "cpus": 8,
        "gpus": 0,
        "disk": 0,
        "price": 6.8729,
        "available": True,
        "microservice": False,
        "machine_learning": False,
        "nice": 0,
        "price_id": "apps.XL",
        "memory": {
          "unit": "B",
          "value": 17179869184,
          "formatted": "16384 MiB"
        }
      },
      {
        "name": "2XL",
        "mem": 24576,
        "cpus": 12,
        "gpus": 0,
        "disk": 0,
        "price": 13.7458,
        "available": True,
        "microservice": False,
        "machine_learning": False,
        "nice": 0,
        "price_id": "apps.2XL",
        "memory": {
          "unit": "B",
          "value": 25769803776,
          "formatted": "24576 MiB"
        }
      },
      {
        "name": "3XL",
        "mem": 32768,
        "cpus": 16,
        "gpus": 0,
        "disk": 0,
        "price": 27.4915,
        "available": True,
        "microservice": False,
        "machine_learning": False,
        "nice": 0,
        "price_id": "apps.3XL",
        "memory": {
          "unit": "B",
          "value": 34359738368,
          "formatted": "32768 MiB"
        }
      }
    ],
    "defaultEnv": {
      "CC_JAVA_VERSION": "11"
    },
    "lifetime": "REGULAR",
    "instanceAndVersion": "java-20221027"
  },
  "deployment": {
    "shutdownable": False,
    "type": "GIT",
    "repoState": "CREATED",
    "url": "git+ssh://git@push-n2-par-clevercloud-customers.services.clever-cloud.com/app_6cb7fded-72d8-4994-b813-c7caa2208019.git",
    "httpUrl": "https://push-n2-par-clevercloud-customers.services.clever-cloud.com/app_6cb7fded-72d8-4994-b813-c7caa2208019.git"
  },
  "vhosts": [
    {
      "fqdn": "dummy-api.domain.com"
    },
    {
      "fqdn": "app-6cb7fded-72d8-4994-b813-c7caa2208019.cleverapps.io"
    },
    {
      "fqdn": "dummy-api.cleverapps.io"
    }
  ],
  "creationDate": 1647960575254,
  "last_deploy": 80,
  "archived": False,
  "stickySessions": False,
  "homogeneous": False,
  "favourite": False,
  "cancelOnPush": True,
  "webhookUrl": None,
  "webhookSecret": None,
  "separateBuild": True,
  "buildFlavor": {
    "name": "XL",
    "mem": 16384,
    "cpus": 8,
    "gpus": 0,
    "disk": None,
    "price": 6.8729,
    "available": True,
    "microservice": False,
    "machine_learning": False,
    "nice": 0,
    "price_id": "apps.XL",
    "memory": {
      "unit": "B",
      "value": 17179869184,
      "formatted": "16384 MiB"
    }
  },
  "ownerId": "orga_f3b3bb57-db31-4dff-8708-0dd91cc31826",
  "state": "SHOULD_BE_UP",
  "commitId": "a8e599c7067e126ddd1885d6eee9be5aebd8a99e",
  "appliance": None,
  "branch": "master",
  "forceHttps": "DISABLED",
  "deployUrl": "git+ssh://git@push-n2-par-clevercloud-customers.services.clever-cloud.com/app_6cb7fded-72d8-4994-b813-c7caa2208019.git"
}
]


CLEVERCLOUD_ADDONS = [
    {
  "id": "addon_f9deff34-d8cc-4bfb-995b-c1d0db37067c",
  "name": "dummy-db-production",
  "realId": "postgresql_9643dfb9-4f46-46bf-9a6c-2ddbf3c5b750",
  "region": "rbxhds",
  "provider": {
    "id": "postgresql-addon",
    "name": "PostgreSQL",
    "website": "http://www.clever-cloud.com",
    "supportEmail": "support@clever-cloud.com",
    "googlePlusName": "",
    "twitterName": "",
    "analyticsId": "",
    "shortDesc": "A powerful, open source object-relational database system",
    "longDesc": "Wanna add an addon to your Clever Cloud account? Want it to be a postgresql database? This is for you!",
    "logoUrl": "https://assets.clever-cloud.com/logos/pgsql.svg",
    "status": "RELEASE",
    "openInNewTab": False,
    "canUpgrade": True,
    "regions": [
      "par",
      "mtl",
      "rbx",
      "wsw",
      "sgp",
      "syd",
      "rbxhds",
      "jed",
      "scw"
    ]
  },
  "plan": {
    "id": "plan_23dd6346-2dda-4951-9c9d-9bba52ed9447",
    "name": "XXS Small Space",
    "slug": "xxs_sml",
    "price": 5.25,
    "price_id": "postgresql.xxs_sml",
    "features": [
      {
        "name": "Migration Tool",
        "type": "BOOLEAN",
        "value": "Yes",
        "computable_value": "true",
        "name_code": "is-migratable"
      },
      {
        "name": "Max connection limit",
        "type": "NUMBER",
        "value": "45",
        "computable_value": "45",
        "name_code": "connection-limit"
      },
      {
        "name": "Metrics",
        "type": "BOOLEAN",
        "value": "Yes",
        "computable_value": "true",
        "name_code": "has-metrics"
      },
      {
        "name": "Max DB size",
        "type": "BYTES",
        "value": "1 GB",
        "computable_value": "1073741824",
        "name_code": "disk-size"
      },
      {
        "name": "Memory",
        "type": "BYTES",
        "value": "512 MB",
        "computable_value": "536870912",
        "name_code": "memory"
      },
      {
        "name": "vCPUS",
        "type": "NUMBER",
        "value": "1",
        "computable_value": "1",
        "name_code": "cpu"
      },
      {
        "name": "Backups",
        "type": "OBJECT",
        "value": "Daily - 7 Retained",
        "computable_value": "{\"frequency_seconds\":86400,\"retention_seconds\":604800}",
        "name_code": "backup"
      },
      {
        "name": "Type",
        "type": "BOOLEAN_SHARED",
        "value": "Dedicated",
        "computable_value": "dedicated",
        "name_code": "is-dedicated"
      },
      {
        "name": "Logs",
        "type": "BOOLEAN",
        "value": "Yes",
        "computable_value": "true",
        "name_code": "has-logs"
      }
    ],
    "zones": [
      "par",
      "mtl",
      "rbx",
      "wsw",
      "sgp",
      "syd",
      "rbxhds",
      "jed",
      "scw"
    ]
  },
  "creationDate": 1658325565658,
  "configKeys": [
    "POSTGRESQL_ADDON_VERSION",
    "POSTGRESQL_ADDON_USER",
    "POSTGRESQL_ADDON_PASSWORD",
    "POSTGRESQL_ADDON_DB",
    "POSTGRESQL_ADDON_HOST",
    "POSTGRESQL_ADDON_PORT",
    "POSTGRESQL_ADDON_URI"
  ],
  "applications": [
    "app_6cb7fded-72d8-4994-b813-c7caa2208019",
  ]
}
]