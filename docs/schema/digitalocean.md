<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Cartography - DigitalOcean Schema](#cartography---digitalocean-schema)
  - [DOAccount](#doaccount)
  - [DOProject](#doproject)
  - [DODroplet](#dodroplet)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Cartography - DigitalOcean Schema

## DOAccount
Representation of a DigitalOcean [Account](https://developers.digitalocean.com/documentation/v2/#account) object.

| Field | Description |
| ----- | ----------- |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The UUID of the Account |
| uuid | The UUID of the Account (same value as id) |
| droplet_limit | Total number of droplets that the Account can have at one time |
| floating_ip_limit | Total number of floating IPs the Account may have |
| status | Status of the Account|

## DOProject
Representation of a DigitalOcean [Project](https://developers.digitalocean.com/documentation/v2/#projects) object.

## DODroplet
Representation of a DigitalOcean [Droplet](https://developers.digitalocean.com/documentation/v2/#droplets) object.