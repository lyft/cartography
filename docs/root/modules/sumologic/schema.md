## Sumologic Schema

.. _sumologic_schema:

### Sumologic core platform

Representation of a system sending logs to Sumologic core platform. Be aware that this may vary depending on your environment.
Default code expects _sourceCategory to be formatted as BU/DC/SOURCE_TYPE aka business unit, datacenter or location, and source type. Source type as SERVER or NXLOG_* to match targeted systems (linux, windows...). Some fields may need to be set through [Field Extraction Rules](https://help.sumologic.com/docs/manage/field-extractions/)

| Field | Description |
|-------|-------------|
|tool_first_seen| Timestamp of when first available logs for host is available since first sync|
|tool_last_seen| Timestamp of when last available logs for host is available per last sync|
|lastupdated| Timestamp of the last time the node was updated|
|**hostname**| The Hostname Computer name|
|short_hostname| The short hostname, lowercase|
|bu| The business unit|
|dc| The datacenter|
