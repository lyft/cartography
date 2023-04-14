# Cartography - ActiveDirectory Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Table of contents

- [ActiveDirectoryHost](#activedirectoryhost)

## ActiveDirectoryHost

Placeholder representation of a single ActiveDirectory Computer as represented by BloodHound and the possible extractors (SharpHound, BloodHound.py, RustHound...).

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| hostname | Computer name |
| short_hostname | standardized short hostname lower-case |
| distinguishedname | distinguishedname |
| enabled | enabled |
| highvalue | highvalue |
| objectid | objectid |
| unconstraineddelegation | unconstraineddelegation |

### Relationships
