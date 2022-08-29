CREATE INDEX ON :AWSConfigurationRecorder(id);
CREATE INDEX ON :AWSConfigDeliveryChannel(id);
CREATE INDEX ON :AWSConfigRule(id);
CREATE INDEX ON :APIGatewayClientCertificate(id);
CREATE INDEX ON :APIGatewayRestAPI(id);
CREATE INDEX ON :APIGatewayResource(id);
CREATE INDEX ON :APIGatewayStage(id);
CREATE INDEX ON :AWSAccount(id);
CREATE INDEX ON :AWSCidrBlock(id);
CREATE INDEX ON :AWSDNSRecord(id);
CREATE INDEX ON :AWSDNSZone(name);
CREATE INDEX ON :AWSDNSZone(zoneid);
CREATE INDEX ON :AWSGroup(arn);
CREATE INDEX ON :AWSInternetGateway(id);
CREATE INDEX ON :AWSIpv4CidrBlock(id);
CREATE INDEX ON :AWSIpv6CidrBlock(id);
CREATE INDEX ON :AWSLambda(id);
CREATE INDEX ON :AWSLambdaEventSourceMapping(id);
CREATE INDEX ON :AWSLambdaFunctionAlias(id);
CREATE INDEX ON :AWSLambdaLayer(id);
CREATE INDEX ON :AWSPeeringConnection(id);
CREATE INDEX ON :AWSPolicy(id);
CREATE INDEX ON :AWSPolicy(name);
CREATE INDEX ON :AWSPolicyStatement(id);
CREATE INDEX ON :AWSPrincipal(arn);
CREATE INDEX ON :AWSRole(arn);
CREATE INDEX ON :AWSTag(id);
CREATE INDEX ON :AWSTag(key);
CREATE INDEX ON :AWSTransitGateway(arn);
CREATE INDEX ON :AWSTransitGateway(id);
CREATE INDEX ON :AWSTransitGatewayAttachment(id);
CREATE INDEX ON :AWSUser(arn);
CREATE INDEX ON :AWSUser(name);
CREATE INDEX ON :AWSVpc(id);
CREATE INDEX ON :AccountAccessKey(accesskeyid);
CREATE INDEX ON :AutoScalingGroup(arn);
CREATE INDEX ON :ChromeExtension(id);
CREATE INDEX ON :Dependency(id);
CREATE INDEX ON :DBGroup(name);
CREATE INDEX ON :DNSRecord(id);
CREATE INDEX ON :DNSZone(name);
CREATE INDEX ON :DOAccount(id);
CREATE INDEX ON :DODroplet(id);
CREATE INDEX ON :DOProject(id);
CREATE INDEX ON :DynamoDBGlobalSecondaryIndex(id);
CREATE INDEX ON :DynamoDBTable(arn);
CREATE INDEX ON :EBSSnapshot(id);
CREATE INDEX ON :EBSVolume(id);
CREATE INDEX ON :DynamoDBTable(id);
CREATE INDEX ON :EC2Image(id);
CREATE INDEX ON :EC2Instance(id);
CREATE INDEX ON :EC2Instance(instanceid);
CREATE INDEX ON :EC2Instance(publicdnsname);
CREATE INDEX ON :EC2KeyPair(id);
CREATE INDEX ON :EC2PrivateIp(id);
CREATE INDEX ON :EC2Reservation(reservationid);
CREATE INDEX ON :EC2ReservedInstance(id);
CREATE INDEX ON :EC2SecurityGroup(groupid);
CREATE INDEX ON :EC2SecurityGroup(id);
CREATE INDEX ON :EC2Subnet(id);
CREATE INDEX ON :EC2Subnet(subnetid);
CREATE INDEX ON :ECRImage(id);
CREATE INDEX ON :ECRRepository(id);
CREATE INDEX ON :ECRRepository(name);
CREATE INDEX ON :ECRRepository(uri);
CREATE INDEX ON :ECRRepositoryImage(id);
CREATE INDEX ON :ECRRepositoryImage(uri);
CREATE INDEX ON :ECRRepositoryImage(tag);
CREATE INDEX ON :ECRScanFinding(id);
CREATE INDEX ON :ECSCluster(id);
CREATE INDEX ON :ECSContainerInstance(id);
CREATE INDEX ON :ECSService(id);
CREATE INDEX ON :ECSTaskDefinition(id);
CREATE INDEX ON :ECSTask(id);
CREATE INDEX ON :ECSContainerDefinition(id);
CREATE INDEX ON :ECSContainer(id);
CREATE INDEX ON :EKSCluster(id);
CREATE INDEX ON :ElasticacheCluster(id);
CREATE INDEX ON :ElasticacheCluster(arn);
CREATE INDEX ON :ElasticIPAddress(id);
CREATE INDEX ON :ELBListener(id);
CREATE INDEX ON :ELBV2Listener(id);
CREATE INDEX ON :EMRCluster(id);
CREATE INDEX ON :EMRCluster(arn);
CREATE INDEX ON :Endpoint(id);
CREATE INDEX ON :ESDomain(arn);
CREATE INDEX ON :ESDomain(id);
CREATE INDEX ON :ESDomain(name);
CREATE INDEX ON :GCPDNSZone(id);
CREATE INDEX ON :GCPRecordSet(id);
CREATE INDEX ON :GCPFolder(id);
CREATE INDEX ON :GCPForwardingRule(id);
CREATE INDEX ON :GCPInstance(id);
CREATE INDEX ON :GCPLabel(id);
CREATE INDEX ON :GCPNetworkInterface(id);
CREATE INDEX ON :GCPNetworkTag(id);
CREATE INDEX ON :GCPNicAccessConfig(id);
CREATE INDEX ON :GCPOrganization(id);
CREATE INDEX ON :GCPProject(id);
CREATE INDEX ON :GCPPrincipal(email);
CREATE INDEX ON :GCPProject(projectnumber);
CREATE INDEX ON :GCPBucket(id);
CREATE INDEX ON :GCPBucketLabel(key);
CREATE INDEX ON :GCPSubnet(id);
CREATE INDEX ON :GCPVpc(id);
CREATE INDEX ON :GCPLocation(id);
CREATE INDEX ON :GCPAPI(id);
CREATE INDEX ON :GCPAPIConfig(id);
CREATE INDEX ON :GCPAPIGateway(id);
CREATE INDEX ON :GCPFunction(id)
CREATE INDEX ON :GCPKMSKeyRing(id);
CREATE INDEX ON :GCPKMSCryptoKey(id);
CREATE INDEX ON :GCPCloudRunAuthorizedDomains(id);
CREATE INDEX ON :GCPCloudRunConfiguration(id);
CREATE INDEX ON :GCPCloudRunDomainMap(id);
CREATE INDEX ON :GCPCloudRunRevision(id);
CREATE INDEX ON :GCPCloudRunRoute(id);
CREATE INDEX ON :GCPCloudRunService(id);
CREATE INDEX ON :GCPRole(id);
CREATE INDEX ON :GCPServiceAccount(id);
CREATE INDEX ON :GCPServiceAccountKey(id);
CREATE INDEX ON :GCPUser(id);
CREATE INDEX ON :GCPCustomer(id);
CREATE INDEX ON :GCPGroup(id);
CREATE INDEX ON :GCPDomain(name);
CREATE INDEX ON :GitHubOrganization(id);
CREATE INDEX ON :GitHubRepository(id);
CREATE INDEX ON :GitHubUser(id);
CREATE INDEX ON :GKECluster(id);
CREATE INDEX ON :GSuiteGroup(email);
CREATE INDEX ON :GSuiteGroup(id);
CREATE INDEX ON :GSuiteUser(email);
CREATE INDEX ON :GSuiteUser(id);
CREATE INDEX ON :GCPSQLInstance(id);
CREATE INDEX ON :GCPSQLUser(id);
CREATE INDEX ON :GCPBigtableInstance(id);
CREATE INDEX ON :GCPBigtableCluster(id);
CREATE INDEX ON :GCPBigtableClusterBackup(id);
CREATE INDEX ON :GCPBigtableTable(id);
CREATE INDEX ON :GCPFirestoreDatabase(id);
CREATE INDEX ON :GCPFirestoreIndex(id);
CREATE INDEX ON :GCPPubsubSubscription(id);
CREATE INDEX ON :GCPPubsubTopic(id);
CREATE INDEX ON :GCPComputeDisk(id);
CREATE INDEX ON :GCPLoggingMetric(id);
CREATE INDEX ON :GCPLoggingSink(id);
CREATE INDEX ON :GCPMonitoringAlertPolicy(id);
CREATE INDEX ON :GCPMonitoringMetricDescriptor(id);
CREATE INDEX ON :GCPMonitoringNotificationChannel(id);
CREATE INDEX ON :GCPMonitoringUptimeCheckConfig(id);
CREATE INDEX ON :GCPDataprocCluster(id);
CREATE INDEX ON :GCPBackendBucket(id);
CREATE INDEX ON :GCPBackendService(id);
CREATE INDEX ON :GCPUrlMap(id);
CREATE INDEX ON :GCPProxy;
CREATE INDEX ON :Ip(id);
CREATE INDEX ON :Ip(ip);
CREATE INDEX ON :IpPermissionInbound(ruleid);
CREATE INDEX ON :IpPermissionsEgress(ruleid);
CREATE INDEX ON :IpRange(id);
CREATE INDEX ON :IpRule(ruleid);
CREATE INDEX ON :JamfComputerGroup(id);
CREATE INDEX ON :KMSKey(id);
CREATE INDEX ON :KMSKey(arn);
CREATE INDEX ON :KMSAlias(id);
CREATE INDEX ON :KMSGrant(id);
CREATE INDEX ON :LaunchConfiguration(id);
CREATE INDEX ON :LaunchConfiguration(name);
CREATE INDEX ON :LaunchTemplate(id);
CREATE INDEX ON :LaunchTemplate(name);
CREATE INDEX ON :LaunchTemplateVersion(id);
CREATE INDEX ON :LaunchTemplateVersion(name);
CREATE INDEX ON :LoadBalancer(dnsname);
CREATE INDEX ON :LoadBalancer(id);
CREATE INDEX ON :LoadBalancerV2(dnsname);
CREATE INDEX ON :LoadBalancerV2(id);
CREATE INDEX ON :NetworkInterface(id);
CREATE INDEX ON :NameServer(id);
CREATE INDEX ON :OktaOrganization(id);
CREATE INDEX ON :OktaUser(id);
CREATE INDEX ON :OktaUser(email);
CREATE INDEX ON :OktaGroup(id);
CREATE INDEX ON :OktaGroup(name);
CREATE INDEX ON :OktaApplication(id);
CREATE INDEX ON :OktaUserFactor(id);
CREATE INDEX ON :OktaTrustedOrigin(id);
CREATE INDEX ON :OktaAdministrationRole(id);
CREATE INDEX ON :Package(id);
CREATE INDEX ON :Package(name);
CREATE INDEX ON :PagerDutyEscalationPolicy(id);
CREATE INDEX ON :PagerDutyEscalationPolicy(name);
CREATE INDEX ON :PagerDutyEscalationPolicyRule(id);
CREATE INDEX ON :PagerDutyIntegration(id);
CREATE INDEX ON :PagerDutySchedule(id);
CREATE INDEX ON :PagerDutySchedule(name);
CREATE INDEX ON :PagerDutyScheduleLayer(id);
CREATE INDEX ON :PagerDutyService(id);
CREATE INDEX ON :PagerDutyService(name);
CREATE INDEX ON :PagerDutyTeam(id);
CREATE INDEX ON :PagerDutyTeam(name);
CREATE INDEX ON :PagerDutyUser(id);
CREATE INDEX ON :PagerDutyUser(name);
CREATE INDEX ON :PagerDutyVendor(id);
CREATE INDEX ON :PagerDutyVendor(name);
CREATE INDEX ON :ProgrammingLanguage(id);
CREATE INDEX ON :PublicIpAddress(ip);
CREATE INDEX ON :PythonLibrary(id);
CREATE INDEX ON :RedshiftCluster(id);
CREATE INDEX ON :RedshiftCluster(arn);
CREATE INDEX ON :RDSCluster(db_cluster_identifier);
CREATE INDEX ON :RDSCluster(id);
CREATE INDEX ON :RDSCluster(arn);
CREATE INDEX ON :RDSInstance(db_instance_identifier);
CREATE INDEX ON :RDSInstance(id);
CREATE INDEX ON :RDSInstance(arn);
CREATE INDEX ON :ReplyUri(id);
CREATE INDEX ON :Risk(id);
CREATE INDEX ON :S3Acl(id);
CREATE INDEX ON :S3Bucket(id);
CREATE INDEX ON :SecretsManagerSecret(id);
CREATE INDEX ON :SecurityHub(id);
CREATE INDEX ON :SQSQueue(id);
CREATE INDEX ON :S3Bucket(name);
CREATE INDEX ON :S3Bucket(arn);
CREATE INDEX ON :User(arn);
CREATE INDEX ON :AzureTenant(id);
CREATE INDEX ON :AzurePrincipal(email);
CREATE INDEX ON :AzureSubscription(id);
CREATE INDEX ON :AzureCosmosDBAccount(id);
CREATE INDEX ON :AzureCosmosDBLocation(id);
CREATE INDEX ON :AzureCosmosDBCorsPolicy(id);
CREATE INDEX ON :AzureCosmosDBAccountFailoverPolicy(id);
CREATE INDEX ON :AzureCDBPrivateEndpointConnection(id);
CREATE INDEX ON :AzureCosmosDBVirtualNetworkRule(id);
CREATE INDEX ON :AzureCosmosDBSqlDatabase(id);
CREATE INDEX ON :AzureCosmosDBCassandraKeyspace(id);
CREATE INDEX ON :AzureCosmosDBMongoDBDatabase(id);
CREATE INDEX ON :AzureCosmosDBTableResource(id);
CREATE INDEX ON :AzureCosmosDBSqlContainer(id);
CREATE INDEX ON :AzureCosmosDBCassandraTable(id);
CREATE INDEX ON :AzureCosmosDBMongoDBCollection(id);
CREATE INDEX ON :AzureStorageAccount(id);
CREATE INDEX ON :AzureStorageQueueService(id);
CREATE INDEX ON :AzureStorageTableService(id);
CREATE INDEX ON :AzureStorageFileService(id);
CREATE INDEX ON :AzureStorageBlobService(id);
CREATE INDEX ON :AzureStorageQueue(id);
CREATE INDEX ON :AzureStorageTable(id);
CREATE INDEX ON :AzureStorageFileShare(id);
CREATE INDEX ON :AzureStorageBlobContainer(id);
CREATE INDEX ON :AzureSQLServer(id);
CREATE INDEX ON :AzureServerDNSAlias(id);
CREATE INDEX ON :AzureServerADAdministrator(id);
CREATE INDEX ON :AzureRecoverableDatabase(id);
CREATE INDEX ON :AzureRestorableDroppedDatabase(id);
CREATE INDEX ON :AzureFailoverGroup(id);
CREATE INDEX ON :AzureElasticPool(id);
CREATE INDEX ON :AzureSQLDatabase(id);
CREATE INDEX ON :AzureReplicationLink(id);
CREATE INDEX ON :AzureDatabaseThreatDetectionPolicy(id);
CREATE INDEX ON :AzureRestorePoint(id);
CREATE INDEX ON :AzureTransparentDataEncryption(id);
CREATE INDEX ON :AzureVirtualMachine(id);
CREATE INDEX ON :AzureDataDisk(id);
CREATE INDEX ON :AzureDisk(id);
CREATE INDEX ON :AzureSnapshot(id);
CREATE INDEX ON :AzureCluster(id);
CREATE INDEX ON :AzureContainerRegistry(id);
CREATE INDEX ON :AzureContainerRegistryReplication(id);
CREATE INDEX ON :AzureContainerRegistryRun(id);
CREATE INDEX ON :AzureContainerRegistryTask(id);
CREATE INDEX ON :AzureContainerRegistryWebhook(id);
CREATE INDEX ON :AzureContainerGroup(id);
CREATE INDEX ON :AzureContainer(id);
CREATE INDEX ON :AzureVirtualMachineExtension(id);
CREATE INDEX ON :AzureVirtualMachineAvailableSize(id);
CREATE INDEX ON :AzureVirtualMachineScaleSet(id);
CREATE INDEX ON :AzureVirtualMachineScaleSetExtension(id);
CREATE INDEX ON :AzureKeyVault(id);
CREATE INDEX ON :AzureUser(id);
CREATE INDEX ON :AzureGroup(id);
CREATE INDEX ON :AzureApplication(id);
CREATE INDEX ON :AzureServiceAccount(id);
CREATE INDEX ON :AzureDomain(id);
CREATE INDEX ON :AzureRole(id);
CREATE INDEX ON :AzureResourceGroup(id);
CREATE INDEX ON :AzureTag(id);
CREATE INDEX ON :AzureNetwork(id);
CREATE INDEX ON :AzureNetworkSubnet(id);
CREATE INDEX ON :AzureRouteTable(id);
CREATE INDEX ON :AzureNetworkRoute(id);
CREATE INDEX ON :AzureNetworkSecurityGroup(id);
CREATE INDEX ON :AzureNetworkSecurityRule(id);
CREATE INDEX ON :AzurePublicIPAddress(id);
CREATE INDEX ON :AzureNetworkUsage(id);
CREATE INDEX ON :AzureFunctionApp(id);
CREATE INDEX ON :AzureFunctionAppConfiguration(id);
CREATE INDEX ON :AzureFunctionAppFunction(id);
CREATE INDEX ON :AzureFunctionAppDeployment(id);
CREATE INDEX ON :AzureFunctionAppProcess(id);
CREATE INDEX ON :AzureFunctionAppBackup(id);
CREATE INDEX ON :AzureFunctionAppSnapshot(id);
CREATE INDEX ON :AzureFunctionAppWebjob(id);
CREATE INDEX ON :KubernetesCluster(id);
CREATE INDEX ON :KubernetesCluster(name);
CREATE INDEX ON :KubernetesNamespace(id);
CREATE INDEX ON :KubernetesNamespace(name);
CREATE INDEX ON :KubernetesPod(id);
CREATE INDEX ON :KubernetesPod(name);
CREATE INDEX ON :KubernetesContainer(id);
CREATE INDEX ON :KubernetesContainer(name);
CREATE INDEX ON :KubernetesContainer(image);
CREATE INDEX ON :KubernetesService(id);
CREATE INDEX ON :KubernetesService(name);
