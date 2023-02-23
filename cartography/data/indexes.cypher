CREATE INDEX IF NOT EXISTS FOR (n:CloudanixWorkspace) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSConfigurationRecorder) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSConfigDeliveryChannel) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSConfigRule) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:APIGatewayClientCertificate) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:APIGatewayRestAPI) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:APIGatewayResource) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:APIGatewayStage) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:APIGatewayClientCertificate) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:APIGatewayStage) ON (n.clientcertificateid);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCloudfrontDistribution) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSAccount) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCidrBlock) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSDNSRecord) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSDNSZone) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:AWSDNSZone) ON (n.zoneid);
CREATE INDEX IF NOT EXISTS FOR (n:AWSGroup) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:AWSInternetGateway) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSIpv4CidrBlock) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSIpv6CidrBlock) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSLambda) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSLambdaEventSourceMapping) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSLambdaFunctionAlias) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSLambdaLayer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSPeeringConnection) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSPolicy) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSPolicy) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:AWSPolicyStatement) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSPrincipal) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:AWSRole) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:AWSTag) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSTag) ON (n.key);
CREATE INDEX IF NOT EXISTS FOR (n:AWSTransitGateway) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:AWSTransitGateway) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSTransitGatewayAttachment) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSUser) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:AWSUser) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:AWSVpc) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCloudWatchAlarm) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCloudWatchFlowLog) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSEventBridgeEventBus) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSEventBridgeRule) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCloudWatchLogGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCloudWatchMetric) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RDSReservedDBInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AccountAccessKey) ON (n.accesskeyid);
CREATE INDEX IF NOT EXISTS FOR (n:AutoScalingGroup) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:ChromeExtension) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:Dependency) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:DBGroup) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:DNSRecord) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:DNSZone) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:DOAccount) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:DODroplet) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:DOProject) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:DynamoDBGlobalSecondaryIndex) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:DynamoDBTable) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:EBSSnapshot) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EBSVolume) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:DynamoDBTable) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Image) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.instanceid);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.publicdnsname);
CREATE INDEX IF NOT EXISTS FOR (n:EC2KeyPair) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2PrivateIp) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Reservation) ON (n.reservationid);
CREATE INDEX IF NOT EXISTS FOR (n:EC2ReservedInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2SecurityGroup) ON (n.groupid);
CREATE INDEX IF NOT EXISTS FOR (n:EC2SecurityGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Subnet) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Subnet) ON (n.subnetid);
CREATE INDEX IF NOT EXISTS FOR (n:ECRImage) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECRRepository) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECRRepository) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:ECRRepository) ON (n.uri);
CREATE INDEX IF NOT EXISTS FOR (n:ECRRepositoryImage) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECRRepositoryImage) ON (n.uri);
CREATE INDEX IF NOT EXISTS FOR (n:ECRRepositoryImage) ON (n.tag);
CREATE INDEX IF NOT EXISTS FOR (n:ECRScanFinding) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECSCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECSContainerInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECSService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECSTaskDefinition) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECSTask) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECSContainerDefinition) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ECSContainer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EKSCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ElasticacheCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ElasticacheCluster) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:EasticIPAddress) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ELBListener) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ELBV2Listener) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:ELBV2Listener) ON (n.lastupdated);
CREATE INDEX IF NOT EXISTS FOR (n:Endpoint) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ESDomain) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:ESDomain) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:ESDomain) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCloudTrailTrail) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSRoute53Domain) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSCloudformationStack) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSSNSTopic) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RedshiftReservedNode) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RDSSecurityGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RDSSnapshot) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSESReservedInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AWSSESIdentity) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPDNSZone) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPDNSPolicy) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPDNSKey) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPLabel) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPRecordSet) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPFolder) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPForwardingRule) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPNetworkInterface) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPNetworkTag) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPNicAccessConfig) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPOrganization) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPProject) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPProject) ON (n.projectnumber);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBucket) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBucketLabel) ON (n.key);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSubnet) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPVpc) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPLocation) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPAPI) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPAPIConfig) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPAPIGateway) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPFunction) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPKMSKeyRing) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPKMSCryptoKey) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCloudRunAuthorizedDomains) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCloudRunConfiguration) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCloudRunDomainMap) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCloudRunRevision) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCloudRunRoute) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCloudRunService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPRole) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPServiceAccount) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPServiceAccountKey) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPUser) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCustomer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPDomain) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:GitHubOrganization) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GitHubRepository) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GitHubUser) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GKECluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GSuiteGroup) ON (n.email);
CREATE INDEX IF NOT EXISTS FOR (n:GSuiteGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GSuiteUser) ON (n.email);
CREATE INDEX IF NOT EXISTS FOR (n:GSuiteUser) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSQLInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSQLUser) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBigtableInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBigtableCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBigtableClusterBackup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBigtableTable) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPFirestoreDatabase) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPFirestoreIndex) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBigqueryDataset) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPBigqueryTable) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPDataFlowJob) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPCloudTasksQueue) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSpannerInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSpannerInstanceConfig) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSpannerInstanceConfigReplica) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSpannerInstanceBackup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPSpannerInstanceDatabase) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPPubSubLiteTopic) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPPubSubLiteSubscription) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:Ip) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:Ip) ON (n.ip);
CREATE INDEX IF NOT EXISTS FOR (n:IpPermissionInbound) ON (n.ruleid);
CREATE INDEX IF NOT EXISTS FOR (n:IpPermissionsEgress) ON (n.ruleid);
CREATE INDEX IF NOT EXISTS FOR (n:IpRange) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:Ipv6Range) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:IpRule) ON (n.ruleid);
CREATE INDEX IF NOT EXISTS FOR (n:JamfComputerGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KMSKey) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KMSKey) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:KMSAlias) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KMSGrant) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:LaunchConfiguration) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:LaunchConfiguration) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:LaunchTemplate) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:LaunchTemplate) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:LaunchTemplateVersion) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:LaunchTemplateVersion) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:LoadBalancer) ON (n.dnsname);
CREATE INDEX IF NOT EXISTS FOR (n:LoadBalancer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:LoadBalancerV2) ON (n.dnsname);
CREATE INDEX IF NOT EXISTS FOR (n:LoadBalancerV2) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:NetworkInterface) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:NameServer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:OktaOrganization) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:OktaUser) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:OktaUser) ON (n.email);
CREATE INDEX IF NOT EXISTS FOR (n:OktaGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:OktaGroup) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:OktaApplication) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:OktaUserFactor) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:OktaTrustedOrigin) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:OktaAdministrationRole) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:Package) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:Package) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyEscalationPolicy) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyEscalationPolicy) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyEscalationPolicyRule) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyIntegration) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutySchedule) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutySchedule) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyScheduleLayer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyService) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyTeam) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyTeam) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyUser) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyUser) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyVendor) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PagerDutyVendor) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:ProgrammingLanguage) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:PublicIpAddress) ON (n.ip);
CREATE INDEX IF NOT EXISTS FOR (n:PythonLibrary) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RedshiftCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RedshiftCluster) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:RDSCluster) ON (n.db_cluster_identifier);
CREATE INDEX IF NOT EXISTS FOR (n:RDSCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RDSCluster) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:RDSInstance) ON (n.db_instance_identifier);
CREATE INDEX IF NOT EXISTS FOR (n:RDSInstance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RDSInstance) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:RDSInstance) ON (n.lastupdated);
CREATE INDEX IF NOT EXISTS FOR (n:RDSSnapshot) ON (n.db_snapshot_identifier);
CREATE INDEX IF NOT EXISTS FOR (n:RDSSnapshot) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:RDSSnapshot) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:RDSSnapshot) ON (n.lastupdated);
CREATE INDEX IF NOT EXISTS FOR (n:ReplyUri) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:Risk) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:S3Acl) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:S3Bucket) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:SecretsManagerSecret) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:SecurityHub) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:SQSQueue) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:S3Bucket) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:S3Bucket) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:User) ON (n.arn);
CREATE INDEX IF NOT EXISTS FOR (n:AzureTenant) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzurePrincipal) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureSubscription) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBAccount) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBLocation) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBCorsPolicy) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBAccountFailoverPolicy) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCDBPrivateEndpointConnection) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBVirtualNetworkRule) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBSqlDatabase) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBCassandraKeySpace) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBMongoDBDatabase) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBTableResource) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBSqlContainer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBCassandraTable) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCosmosDBMongoDBCollection) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageAccount) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageQueueService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageTableService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageFileService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageBlobService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageQueue) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageTable) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageFileShare) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureStorageBlobContainer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureSQLServer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureServerDNSAlias) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureServerADAdministrator) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureRecoverableDatabase) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureRestorableDroppedDatabase) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFailoverGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureElasticPool) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureSQLDatabase) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureReplicationLink) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureDatabaseThreatDetectionPolicy) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureRestorePoint) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureTransparentDataEncryption) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureVirtualMachine) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureDataDisk) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureDisk) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureSnapshot) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:GCPDomain) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureContainerRegistry) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureContainerRegistryReplication) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureContainerRegistryRun) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureContainerRegistryTask) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureContainerRegistryWebhook) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureContainerGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureContainer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureVirtualMachineExtension) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureVirtualMachineAvailableSize) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureVirtualMachineScaleSet) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureVirtualMachineScaleSetExtension) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureKeyVault) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureUser) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureApplication) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureServiceAccount) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureDomain) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureRole) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureResourceGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureTag) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureNetwork) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureNetworkSubnet) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureRouteTable) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureNetworkRoute) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureNetworkSecurityGroup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureNetworkSecurityRule) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzurePublicIPAddress) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureNetworkUsage) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionApp) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionAppConfiguration) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionAppFunction) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionAppDeployment) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionAppProcess) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionAppBackup) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionAppSnapshot) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunctionAppWebJob) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureMonitorLogProfile) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureKeyVaultKey) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureKeyVaultSecret) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureKeyVaultCertificate) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureSecurityContact) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesCluster) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesCluster) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesNamespace) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesNamespace) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesPod) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesPod) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesContainer) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesContainer) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesContainer) ON (n.image);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesService) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:KubernetesService) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:AzureFunction) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:AzureLocation) ON (n.id);
