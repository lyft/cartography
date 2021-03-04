<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [DigitalOcean Configuration](#digitalocean-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# DigitalOcean Configuration

Follow these steps to analyze GitHub repos and other objects with Cartography.

1. Prepare your DigitalOcean credentials.
1. Populate an environment variable of your choice with the contents from the previous step.
1. Call the `cartography` CLI with `--digitalocean-token-env-var YOUR_ENV_VAR_HERE`.
1. `cartography` will then load your graph with data from all the organizations you specified.
