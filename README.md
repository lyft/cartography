# Cartography
Cartography is a Python tool that consolidates infrastructure assets and the relationships between them in an intuitive graph view powered by a [Neo4j](https://www.neo4j.com) database.

![Visualization of RDS nodes and AWS nodes](docs/images/accountsandrds.png)

## Why Cartography?
Cartography aims to enable a broad set of exploration and automation scenarios.  It is particularly good at exposing otherwise hidden dependency relationships between your service's assets so that you may validate assumptions about security risks.

Service owners can generate asset reports, Red Teamers can discover attack paths, and Blue Teamers can identify areas for security improvement.   All can benefit from using the graph for manual exploration through a web frontend interface, or in an automated fashion by calling the APIs.

Cartography is not the only [security](https://github.com/dowjones/hammer) [graph](https://github.com/BloodHoundAD/BloodHound) [tool](https://github.com/Netflix/security_monkey) [out](https://github.com/vysecurity/ANGRYPUPPY) [there](https://github.com/duo-labs/cloudmapper), but it differentiates itself by being fully-featured yet generic and [extensible](docs/dev/writing-analysis-jobs.md) enough to help make anyone better understand their risk exposure, regardless of what platforms they use.  Rather than being focused on one core scenario or attack vector like the other linked tools, Cartography focuses on flexibility and exploration.

You can learn more about the story behind Cartography in our [presentation at BSidesSF 2019](https://www.youtube.com/watch?v=ZukUmZSKSek).

## Install and configure
Start [here](docs/setup/install.md).

## Supported platforms
- [Amazon Web Services](docs/setup/config/aws.md) -  EC2, Elasticsearch, DynamoDB, IAM,  RDS, Route53, S3, STS 
- [Google Cloud Platform](docs/setup/config/gcp.md) - Cloud Resource Manager, Compute, Storage
- [Google GSuite](docs/setup/config/gsuite.md) - users, groups
- [Duo CRXcavator](docs/setup/config/crxcavator.md) - Chrome extensions, GSuite users 
- [Okta](docs/setup/config/okta.md) - users, groups, organizations, roles, applications, factors, trusted origins, reply URIs
- [Github](docs/setup/config/github.md) - repos, branches, users

## Usage
Start with our [tutorial](docs/usage/tutorial.md).

## Contact

Slack: go [here]() to get invited to our Slack channel.

## Contributing
Thank you for considering contributing to Cartography!

### Code of conduct
Legal stuff: This project is governed by [Lyft's code of conduct](https://github.com/lyft/code-of-conduct).
All contributors and participants agree to abide by its terms.

### Developing Cartography

Get started with our [developer documentation](docs/dev/developer-guide.md).


#### Sign the Contributor License Agreement (CLA)

We require a CLA for code contributions, so before we can accept a pull request
we need to have a signed CLA. Please [visit our CLA service](https://oss.lyft.com/cla)
and follow the instructions to sign the CLA.
