<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Microsoft Azure Configuration](#microsoft-azure-configuration)
    - [Single Subscription Setup](#single-subscription-setup)
    - [Multiple Subscription Setup](#multiple-subscription-setup)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Microsoft Azure Configuration

Follow these steps to analyze Microsoft Azure assets with Cartography.

### Single Subscription Setup

1. Set up an Azure identity (user) for Cartography to use. Ensure that this identity has the built-in Azure [Reader role](https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#reader) attached.  This Role grants access to read resources metadata.
1. Set up Azure credentials to this identity on your server, using a `az login`.  For details, see Azure' [official guide](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli).


### Multiple Subscription Setup
To allow Cartography to pull from more than one Subscription, grant Reader Role to the user for each subscriptions.
