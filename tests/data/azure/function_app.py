DESCRIBE_FUNCTIONAPPS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
        "type": "Microsoft.Web/sites",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestFunctionApp1",
        "container_size": 1234,
        "default_host_name": "abc.azurewebsites.net",
        "last_modified_time_utc": "2021-10-15T13:30:13.61",
        "state": "Running",
        "repository_site_name": "ABC-LOGS-PROCESSING",
        "daily_memory_time_quota": 0,
        "availability_state": "Normal",
        "usage_state": "Normal",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
        "type": "Microsoft.Web/sites",
        "location": "West US",
        "resource_group": "TestRG",
        "name": "TestFunctionApp2",
        "container_size": 1234,
        "default_host_name": "ab2.azurewebsites.net",
        "last_modified_time_utc": "2020-10-15T13:30:13.61",
        "state": "Running",
        "repository_site_name": "ABC2-LOGS-PROCESSING",
        "daily_memory_time_quota": 0,
        "availability_state": "Normal",
        "usage_state": "Normal",
    },
]

DESCRIBE_FUNCTIONAPPCONFIGURATIONS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/config/Conf1",
        "type":
        "Microsoft.Web/sites/config",
        "location":
        "West US",
        "resource_group":
        "TestRG",
        "name":
        "Conf1",
        "number_of_workers":
        1,
        "net_framework_version":
        "",
        "php_version":
        "",
        "python_version":
        "Python 3.8",
        "node_version":
        "",
        "linux_fx_version":
        "PYTHON|3.8",
        "windows_fx_version":
        "",
        "request_tracing_enabled":
        False,
        "remote_debugging_enabled":
        True,
        "logs_directory_size_limit":
        1234,
        "java_version":
        "",
        "auto_heal_enabled":
        False,
        "vnet_name":
        "CDS",
        "local_my_sql_enabled":
        False,
        "ftps_state":
        "AllAllowed",
        "pre_warmed_instance_count":
        465,
        "health_check_path":
        "cds-fds.net",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/config/Conf2",
        "type":
        "Microsoft.Web/sites/config",
        "location":
        "West US",
        "resource_group":
        "TestRG",
        "name":
        "Conf2",
        "number_of_workers":
        1,
        "net_framework_version":
        "",
        "php_version":
        "",
        "python_version":
        "Python 3.8",
        "node_version":
        "",
        "linux_fx_version":
        "PYTHON|3.8",
        "windows_fx_version":
        "",
        "request_tracing_enabled":
        False,
        "remote_debugging_enabled":
        True,
        "logs_directory_size_limit":
        1234,
        "java_version":
        "",
        "auto_heal_enabled":
        False,
        "vnet_name":
        "CDS",
        "local_my_sql_enabled":
        False,
        "ftps_state":
        "AllAllowed",
        "pre_warmed_instance_count":
        465,
        "health_check_path":
        "cds-fds.net",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    },
]

DESCRIBE_FUNCTIONAPPFUNCTIONS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/functions/functon1",
        "type":
        "Microsoft.Web/sites/functions",
        "resource_group":
        "TestRG",
        "name":
        "function1",
        "href":
        "ads-dgs.net",
        "language":
        ".net",
        "is_disabled":
        False,
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/functions/functon2",
        "type":
        "Microsoft.Web/sites/functions",
        "resource_group":
        "TestRG",
        "name":
        "function2",
        "href":
        "ads-dgs.net",
        "language":
        ".net",
        "is_disabled":
        False,
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    },
]

DESCRIBE_FUNCTIONAPPDEPLOYMENTS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/deployments/deploy1",
        "type":
        "Microsoft.Web/sites/deployments",
        "resource_group":
        "TestRG",
        "name":
        "deploy1",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/deployments/deploy2",
        "type":
        "Microsoft.Web/sites/deployments",
        "resource_group":
        "TestRG",
        "name":
        "deploy2",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    },
]

DESCRIBE_FUNCTIONAPPBACKUPS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/backups/backup1",
        "type":
        "Microsoft.Web/sites/backups",
        "resource_group":
        "TestRG",
        "name":
        "backup1",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/backups/backup2",
        "type":
        "Microsoft.Web/sites/backups",
        "resource_group":
        "TestRG",
        "name":
        "backup2",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    },
]

DESCRIBE_FUNCTIONAPPPROCESSES = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/processes/process1",
        "type":
        "Microsoft.Web/sites/processes",
        "resource_group":
        "TestRG",
        "name":
        "process1",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/processes/process2",
        "type":
        "Microsoft.Web/sites/processes",
        "resource_group":
        "TestRG",
        "name":
        "backup2",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    },
]

DESCRIBE_FUNCTIONAPPSNAPSHOTS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/snapshots/snap1",
        "type":
        "Microsoft.Web/sites/snapshots",
        "resource_group":
        "TestRG",
        "name":
        "snap1",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/snapshots/snap2",
        "type":
        "Microsoft.Web/sites/snapshots",
        "resource_group":
        "TestRG",
        "name":
        "snap2",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    },
]

DESCRIBE_FUNCTIONAPPWEBJOBS = [
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp1/webjobs/webjob1",
        "type":
        "Microsoft.Web/sites/webjobs",
        "resource_group":
        "TestRG",
        "name":
        "webjob1",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp1",
    },
    {
        "id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/\
            TestFunctionApp2/webjobs/webjob2",
        "type":
        "Microsoft.Web/sites/webjobs",
        "resource_group":
        "TestRG",
        "name":
        "webjob2",
        "function_app_id":
        "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/TestFunctionApp2",
    },
]
