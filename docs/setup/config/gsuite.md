<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Google GSuite Configuration](#google-gsuite-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Google GSuite Configuration

Follow these steps to analyze GSuite users and groups with Cartography.

1.  Prepare your GSuite Credential.

    Ingesting GSuite Users and Groups utilizes the [Google Admin SDK](https://developers.google.com/admin-sdk/).

    1. [Enable Google API access](https://support.google.com/a/answer/60757?hl=en)
    1. Create a new G Suite user account and accept the Terms of Service. This account will be used as the domain-wide delegated access.
    1. [Perform G Suite Domain-Wide Delegation of Authority](https://developers.google.com/admin-sdk/directory/v1/guides/delegation)
    1.  Download the service account's credentials
    1.  Export the environmental variables:
        1. `GSUITE_GOOGLE_APPLICATION_CREDENTIALS` - location of the credentials file.
        1. `GSUITE_DELEGATED_ADMIN` - email address that you created in step 2
