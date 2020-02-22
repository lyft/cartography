<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [CRXCavator Configuration](#crxcavator-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# CRXCavator Configuration

Follow these steps to analyze Chrome Extensions with Cartography.

1. **Prepare your CRXcavator API key**

    1. Generate an API key from your CRXcavator [user page](https://crxcavator.io/user/settings#)
    1. Add the required commandline arguments when calling Cartography
        1. `--crxcavator-api-base-url` - the full URL to the CRXcavator API. https://api.crxcavator.io/v1 as of 01/16/2020 (this value will be used if not provided)
        1. `--crxcavator-api-key-env-var` - Name of environment variable holding your API key generated in the previous step. Note this is a credential and should be stored in an appropriate secret store to be populated securely into your runtime environment.
