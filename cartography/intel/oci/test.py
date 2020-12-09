#Copyright (c) 2020, Oracle and/or its affiliates.
import oci
import re
config = oci.config.from_file("~/.oci/config","DEFAULT")
compartment_id_root = config["tenancy"]
user_id = config["user"]
identity = oci.identity.IdentityClient(config)

def get_compartment_list_data_recurse(iam, compartment_list, compartment_id):
    response = oci.pagination.list_call_get_all_results(iam.list_compartments,compartment_id)
    if not response.data:
        return
    compartment_list.update({"Compartments":list(compartment_list["Compartments"])+response.data})
    for compartment in response.data:
        get_compartment_list_data_recurse(iam, compartment_list, compartment.id)


compartment_list={"Compartments":""}
get_compartment_list_data_recurse(identity,compartment_list,compartment_id_root)

print(len(compartment_list["Compartments"]))
print(len(oci.pagination.list_call_get_all_results(identity.list_compartments,compartment_id_root).data))

exit()

user_groups=[]
response = oci.pagination.list_call_get_all_results(identity.list_user_group_memberships, compartment_id=compartment_id_root,user_id=user_id)
for group in response.data:
    #print(group)
    user_groups.append(identity.get_group(group.group_id).data.name)

print(user_groups)

policy_statements=[]
response = oci.pagination.list_call_get_all_results(identity.list_policies, compartment_id=compartment_id_root)
for policy in response.data:
    for statement in policy.statements:
        for group in user_groups:
            m=re.search("Allow group "+group+" to inspect all-resources in tenancy",statement,re.IGNORECASE)
            if(m):
                print(m.group())
            m=re.search("Allow group "+group+" to read instances in tenancy",statement,re.IGNORECASE)
            if(m):
                print(m.group())
            m=re.search("Allow group "+group+" to read audit-events in tenancy",statement,re.IGNORECASE)
            if(m):
                print(m.group())

exit()
response = oci.pagination.list_call_get_all_results(identity.list_compartments, compartment_id=compartment_id_root)
for instance in response.data:
    print('Id: {}'.format(instance.id))
    test = oci.pagination.list_call_get_all_results(identity.list_compartments, compartment_id=instance)
    for instance2 in test.data:
        print('Id: {}'.format(instance2.id))

exit()

print(config)

lol=[]
response = oci.pagination.list_call_get_all_results(identity.list_users, compartment_id_root)
for user in response.data:
    #print('User: {}'.format(compartment_id.id))
    print(user)
exit()
    #lol.append(compartment_id.id)
    #computeClient = oci.core.ComputeClient(config)
    #response = oci.pagination.list_call_get_all_results(computeClient.list_instances, compartment_id=compartment_id.id)
    #for instance in response.data:
    #    print('Id: {}'.format(instance.id))

print("lol")
computeClient=oci.core.ComputeClient(config)
response = oci.pagination.list_call_get_all_results(computeClient.list_instances, compartment_id=compartment_id_root)
for instance in response.data:
    print('Id: {}'.format(instance.id))


exit()

computeClient=oci.core.ComputeClient(config)
response = oci.pagination.list_call_get_all_results(computeClient.list_instances, compartment_id=compartment_id)
for instance in response.data:
    print('Id: {}'.format(instance.id))

blockStorage=oci.core.BlockstorageClient(config)
response = oci.pagination.list_call_get_all_results(blockStorage.list_volumes, compartment_id=compartment_id)
for volume in response.data:
    print('Id: {}'.format(volume.id))
