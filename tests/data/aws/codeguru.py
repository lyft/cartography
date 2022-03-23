import datetime

GET_REPOSITORY_ASSOCIATIONS = [
    {
        'AssociationArn': 'AssociationArn001',
        'ConnectionArn': 'string',
        'LastUpdatedTimeStamp': datetime.datetime(2022, 1, 1),
        'AssociationId': 'AssociationId001',
        'Name': 'string',
        'Owner': 'test-001',
        'ProviderType': 'GitHub',
        'State': 'Associated',
    },
    {
        'AssociationArn': 'AssociationArn002',
        'ConnectionArn': 'string',
        'LastUpdatedTimeStamp': datetime.datetime(2022, 1, 1),
        'AssociationId': 'AssociationId002',
        'Name': 'string',
        'Owner': 'test-002',
        'ProviderType': 'GitHub',
        'State': 'Associated',
    },
]

GET_CODE_REVIEWS = [
    {
        'CodeReviewArn': 'AssociationArn001:code-review:PR-GIT-aws-cdg-reviewer-sample-app-1',
        'AssociationArn': 'AssociationArn001',
        'PullrequestId': '2',
        'LastUpdatedTimeStamp': datetime.datetime(2022, 1, 1),
        'Name': 'GIT-aws-cdg-reviewer-sample-app-1',
        'Owner': 'test-001',
        'RepositoryName': 'amazon-codeguru-reviewer-sample-app',
        'ProviderType': 'GitHub',
        'State': 'Completed',
        'Type': 'PullRequest',
    },
    {
        'CodeReviewArn': 'AssociationArn002:code-review:PR-GIT-aws-cdg-reviewer-sample-app-2',
        'AssociationArn': 'AssociationArn002',
        'PullrequestId': '1',
        'LastUpdatedTimeStamp': datetime.datetime(2022, 1, 1),
        'Name': 'GIT-aws-cdg-reviewer-sample-app-2',
        'Owner': 'test-002',
        'RepositoryName': 'amazon-codeguru-reviewer-sample-app',
        'ProviderType': 'GitHub',
        'State': 'Completed',
        'Type': 'PullRequest',
    },
]

GET_RECOMMENDATIONS = [
    {
        'Description': 'desc001',
        'LastUpdatedTimeStamp': datetime.datetime(2022, 1, 1),
        'StartLine': '10',
        'EndLine': '11',
        'FilePath': 'src/main/java/com/demo/EventHandler.java',
        'RecommendationId': 'rrr001',
        'CodeReviewArn': 'AssociationArn001:code-review:PR-GIT-aws-cdg-reviewer-sample-app-1',
        'RecommendationCategory': 'AWSBestPractices',
    },
    {
        'Description': 'desc002',
        'LastUpdatedTimeStamp': datetime.datetime(2022, 1, 1),
        'StartLine': '20',
        'EndLine': '22',
        'FilePath': 'src/main/java/com/demo/TestHandler.java',
        'RecommendationId': 'rrr002',
        'CodeReviewArn': 'AssociationArn002:code-review:PR-GIT-aws-cdg-reviewer-sample-app-2',
        'RecommendationCategory': 'AWSBestPractices',
    },
]
