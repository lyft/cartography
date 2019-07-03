# How to use Drift-Detection

## Intro
Drift-Detection is a separate module from cartography which allows you to automate the detection of mutations in your infrastructure after cartography has been run. 

### How to run
Queries and their expected results are stored in the form of drift state objects which contain a name, query, type, list of properties, and list of values. When running drift-detection, you should specify a drift detection directory as an input.

In the specified directory, each query should have a designated subdirectory with a drift state template named "template.json", containing its name, validation query, query properties, and a blank results field. 
After running an update, results will be stored as lists, and properties of results with multiple fields will have their fields concatenated in the created json files.

```
{
  "name": "Sample Template",
  "validation_query": "MATCH (n) RETURN n.property_1, n.property_2, n.property_3",
  "properties": ["n.property_1", "n.property_2", "n.property_3"],
  "expectations": []
}
```

```
{
  "name": "Sample File After Update",
  "validation_query": "MATCH (n) RETURN n.property_1, n.property_2, n.property_3",
  "properties": ["n.property_1", "n.property_2", "n.property_3"],
  "detector_type": 1,
  "expectations": [
    ["detector_1.property_1", "detector_1.property_2", "detector_1.concatenated_property_3|detector_1.concatenated_property_3|detector_1.concatenated_property_3", ...],
    ["detector_2.property_1", "detector_2.property_2", "detector_2.concatenated_property_3|detector_2.concatenated_property_3|detector_2.concatenated_property_3", ...],
    ...
  ]
}
```

There should also be a file called "report_info.json" stored in the directory which will provide miscellaneous information for drift-detection. This file should contain the same name, the detector type as an integer, and an empty dictionary of shortcuts.

```
{
    "name": "Sample Template",
    "detector_type": 1,
    "shortcuts": {}
}
```

Once all query files have been created and stored in a directory, we can save the state of each of the queries by running:

`cartography-detectdrift update --neo4j-uri <your neo4j uri> --drift-detection-directory <path to directory containing all query files>`

To compare states and get the drift information between them, we can run the command:

`cartography-detectdrift get-drift --query-directory <path to query directory> --start-state <filename of first state to compare, no directory prefix> --end-state <filename of end state to compare, no directory prefix>`

We can also add shortcuts to important files by running the command:

`cartography-detectdrift add-shortcut --query-directory <path to query directory> --shortcut <name of shortcut> --file <driftstate file to shortcut, no directory prefix>`

Now when we run the `get-drift` command, we can replace the name of the file with the shortcut to it. The most recent file in each query directory is by default added after each update and can be accessed with the shortcut `most-recent`.

## Example Detector File: how many more of my EC2 instances are accessible to any host on the internet?
Let's say we're interested in the internet exposure command from the analysis job example. We've determined that monitoring the growth/decline of internet exposed instances will be important to us maintaining secure architecture in the future and we want to store these results and track them over time. The good news is drift-detection will allow us to do just that!

First we create a template file and report info file in the formats shown above.

```
{
  "name": "Internet Exposed EC2 Instances",
  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type"
  "properties": ["n.instancetype", "n.privateipaddress", "n.publicdnsname", "n.exposed_internet_type"],
  "results": []
}
```

```
{
  "name": "Internet Exposed EC2 Instances",
  "detector_type": 1,
  "shortcuts": {}
}
```

We save these two files in a directory `<query_directory>` in our drift detection directory, `<driftdirectory>`. Our infrastructure is saved in a neo4j database accessed by `<neo4j_uri>`.
Now let's say running the validation query in neo4j produces these results:

```
| n.instancetype 	| n.privateipaddress 	| n.publicdnsname             	| n.exposed_internet_type 	|
|----------------	|--------------------	|-----------------------------	|-------------------------	|
| c4.large       	| 10.255.255.251     	| ec2.1.compute.amazonaws.com 	| [direct]                	|
| t2.micro       	| 10.255.255.252     	| ec2.2.compute.amazonaws.com 	| [direct]                	|
| c4.large       	| 10.255.255.253     	| ec2.3.compute.amazonaws.com 	| [direct, elb]                	|
| t2.micro       	| 10.255.255.254     	| ec2.4.compute.amazonaws.com 	| [direct, elb]                 |

```
We then execute the update command in cartography:

`cartography-detectdrift update --neo4j-uri <neo4j_uri> --drift-detection-directory <driftdirectory>`

After running the update command in cartography, we should now see a new JSON file `<first_date>.json` saved with information in this format:

```
{
  "name": "Internet Exposed EC2 Instances",
  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type"
  "properties": ["n.instancetype", "n.privateipaddress", "n.publicdnsname", "n.exposed_internet_type"],
  "results": [
    ["c4.large", "10.255.255.251", "ec2.1.compute.amazonaws.com", "direct"],
    ["t2.micro", "10.255.255.252", "ec2.2.compute.amazonaws.com", "direct"],
    ["c4.large", "10.255.255.253", "ec2.3.compute.amazonaws.com", "direct|elb"],
    ["t2.micro", "10.255.255.254", "ec2.4.compute.amazonaws.com", "direct|elb"]
  ]
}
```

Now let's say it's been a couple days, and some new EC2 Instances were added. We run the update command once more and get another file `<second_date>.json` which looks like this:

```
{
  "name": "Internet Exposed EC2 Instances",
  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type""
  "properties": ["n.instancetype", "n.privateipaddress", "n.publicdnsname", "n.exposed_internet_type"],
  "results": [
    ["c4.large", "10.255.255.251", "ec2.1.compute.amazonaws.com", "direct"],
    ["t2.micro", "10.255.255.252", "ec2.2.compute.amazonaws.com", "direct"],
    ["c4.large", "10.255.255.253", "ec2.3.compute.amazonaws.com", "direct|elb"],
    ["c4.large", "10.255.255.255", "ec2.5.compute.amazonaws.com", "direct|elb"]
  ]
}
```

It looks like our results list has slightly changed. We can add shortcuts to be able to access these two files without specifying the filename. This lets us bookmark certain states with whatever name we want. Let's say we want to bookmark the first update by "first-run" and the second update by "most-recent". To do so we run:

`cartography-detectdrift add-shortcut --shortcut first-run --file <first_date>.json`
`cartography-detectdrift add-shortcut --shortcut second-recent --file <second_date>.json`

Now to get the drift information between the two files, we can run

`cartography-detectdrift get-drift --query-directory <query_directory> --start-state <first_date>.json --end-state <second_date>.json`

or to make use of the shortcuts we added,

`cartography-detectdrift get-drift --query-directory <query_directory> --start-state first-run --end-state second-run`.

Finally, we should see the following messages pop up:

```
New Drift Information:

Detector Name: Internet Exposed EC2 Instances
Detector Type: DriftDetectorType.EXPOSURE
Drift Information: {'n.instancetype': 'c4.large', 'n.privateipaddress': '10.255.255.255', 'n.publicdnsname': 'ec2.5.compute.amazonaws.com', 'n.exposed_internet_type': ['direct', elb']}

Missing Drift Information:

Detector Name: Internet Exposed EC2 Instances
Detector Type: DriftDetectorType.EXPOSURE
Drift Information: {'n.instancetype': 't2.micro', 'n.privateipaddress': '10.255.255.253', 'n.publicdnsname': 'ec2.4.compute.amazonaws.com', 'n.exposed_internet_type': ['direct', elb']}
```
