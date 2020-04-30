<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Oracle Cloud Infrastructure](#oci-web-services-configuration)
    - [Single OCI Tenancy Setup](#single-oci-account-setup)
    - [Multiple OCI Tenancy Setup](#multiple-oci-account-setup)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Oracle Cloud Infrastructure Configuration

Follow these steps to analyze OCI assets with Cartography.

### Single AWS Tenancy Setup

1. If you're a OCI user, **prepare your OCI credential(s)**

    1. Create an OCI Identity in your Tenancy for Cartography to run as
    2. Ensure that this identity has the following policy for Auditors (https://docs.cloud.oracle.com/iaas/Content/Identity/Concepts/commonpolicies.htm) attached to it:
        - `Allow group Auditors to inspect all-resources in tenancy`
        - `Allow group Auditors to read instances in tenancy`
        - `Allow group Auditors to read audit-events in tenancy`
    3. Ensure that the machine you are running Cartography on can authenticate to this identity.
        - Set up OCI credentials to this identity on your server, using a `config` file.  For details, see OCI's [official guide](https://docs.cloud.oracle.com/iaas/Content/API/SDKDocs/cliinstall.htm).
    4. **If you want to pull from multiple OCI Tenancies**, see [here](#multiple-oci-tenancy-setup).

 ### Multiple OCI Tenancy Setup
1. Add a profile for each OCI Tenancy you want Cartography to sync with to your `config`.  It will look something like this:
    ```
   [tenancy1]
   user=ocid1.user.oc1..9q8z3bdjhie1pkazptpymaif87a6h9ci6gw71n0waeehk7u4kku447zeamd5
   fingerprint=3a:ff:f5:4c:b8:26:85:94:bb:d3:f8:a3:01:25:6f:29
   key_file=/home/user/.oci/oci_api_key.pem
   tenancy=ocid1.tenancy.oc1..e1pkazptpymaif9q8z3bdjhi87a6h9ci6gw71n0waeehk7u4kku447zeamd5
   region=us-phoenix-1
   [tenancy2]
   user=ocid1.user.oc1..hie1pkazptpymaif9q8z3bdj87a6h9ci6gw71n0waeehk7u4kku447zeamd5
   fingerprint=3a:ff:f5:4c:b8:26:85:94:bb:d3:f8:a3:01:25:6f:29
   key_file=/home/user/.oci/oci_api_key.pem
   tenancy=ocid1.tenancy.oc1..1n0waeehk7u4kke1pkazptpymaif9q8z3bdjhi87a6h9ci6gw7u447zeamd5
   region=us-phoenix-1
   
   ... etc ...
   ```
   Please note that when the `--oci-sync-all-profiles` flag is enabled it will skill the `DEFAULT` profile in the OCI `config`.