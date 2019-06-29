# How to use Drift-Detection

## Intro
Drift-Detection is a separate module from cartography which allows you to automate the detection of changes in expectations of your infrastructure after cartography has been run. 

### How to run
Queries and their expected results are stored in the form of detectors. Each detector is stored in a JSON file which contains the name of the detector, its specific validation query, its type, and the expected results of running its query. Expected results will be stored as lists, and properties of results with multiple fields will have their fields concatenated.
```
{
  "name": "Sample Detector",
  "validation_query": "MATCH (n) RETURN n.property_1, n.property_2, n.property_3",
  "detector_type": 1,
  "expectations": [
    ["detector_1.property_1", "detector_1.property_2", "detector_1.concatenated_property_3|detector_1.concatenated_property_3|detector_1.concatenated_property_3", ...],
    ["detector_2.property_1", "detector_2.property_2", "detector_2.concatenated_property_3|detector_2.concatenated_property_3|detector_2.concatenated_property_3", ...],
    ...
  ]
}
```

Once all detector files have been created and stored in a directory, drift detection can be run with the following command:

`cartography-detectdrift --neo4j-uri <your neo4j uri> --drift-detector-directory <your directory containing all detector files>`

## Example Detector File: how many more of my EC2 instances are accessible to any host on the internet?
Let's say we've run the internet exposure command from the analysis job example and these are our results:
```
| n.instancetype 	| n.privateipaddress 	| n.publicdnsname             	| n.exposed_internet_type 	|
|----------------	|--------------------	|-----------------------------	|-------------------------	|
| c4.large       	| 10.255.255.251     	| ec2.1.compute.amazonaws.com 	| [direct]                	|
| t2.micro       	| 10.255.255.252     	| ec2.2.compute.amazonaws.com 	| [direct]                	|
| c4.large       	| 10.255.255.253     	| ec2.3.compute.amazonaws.com 	| [direct, elb]                	|
| t2.micro       	| 10.255.255.254     	| ec2.4.compute.amazonaws.com 	| [direct, elb]                 |

```

We want to store these results to compare against in the future, so we save them in a Detector file in our designated directory like so:
```
{
  "name": "Internet Exposed EC2 Instances",
  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type""
  "detector_type": 1,
  "expectations": [
    ["c4.large", "10.255.255.251", "ec2.1.compute.amazonaws.com", "direct"],
    ["t2.micro", "10.255.255.252", "ec2.2.compute.amazonaws.com", "direct"],
    ["c4.large", "10.255.255.253", "ec2.3.compute.amazonaws.com", "direct|elb"],
    ["t2.micro", "10.255.255.254", "ec2.4.compute.amazonaws.com", "direct|elb"]
  ]
}
```

Now let's say it's been a couple days, and some new EC2 Instances were added. Executing the command results in this stdout
```
Detector Name: Internet Exposed EC2 Instances
Detector Type: DriftDetectorType.EXPOSURE
Drift Information: {'n.instancetype': 'c4.large', 'n.privateipaddress': '10.255.255.255', 'n.publicdnsname': 'ec2.5.compute.amazonaws.com', 'n.exposed_internet_type': ['direct', elb']}
```
We now see that another internet exposed instance has appeared in our infrastructure. We can choose to update the previous detectors by running 
`cartography-detectdrift --neo4j-uri <your neo4j uri> --drift-detector-directory <your directory containing all detector files> --update`.

```
{
  "name": "Internet Exposed EC2 Instances",
  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type""
  "detector_type": 1,
  "expectations": [
    ["c4.large", "10.255.255.251", "ec2.1.compute.amazonaws.com", "direct"],
    ["t2.micro", "10.255.255.252", "ec2.2.compute.amazonaws.com", "direct"],
    ["c4.large", "10.255.255.253", "ec2.3.compute.amazonaws.com", "direct|elb"],
    ["t2.micro", "10.255.255.254", "ec2.4.compute.amazonaws.com", "direct|elb"],
    ["c4.large", "10.255.255.255", "ec2.5.compute.amazonaws.com", "direct|elb"]
  ]
}
```