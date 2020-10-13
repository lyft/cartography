import datetime

from okta.models.user.User import User
from okta.models.user.UserProfile import UserProfile


def create_test_user():
    user = User()

    user.id = "userid"
    user.activated = datetime.datetime(2019, 1, 1, 0, 0, 1)
    user.created = datetime.datetime(2019, 1, 1, 0, 0, 1)
    user.activated = datetime.datetime(2019, 1, 1, 0, 0, 1)
    user.statusChanged = datetime.datetime(2019, 1, 1, 0, 0, 1)
    user.lastLogin = datetime.datetime(2019, 1, 1, 0, 0, 1)
    user.lastUpdated = datetime.datetime(2019, 1, 1, 0, 0, 1)
    user.passwordChanged = datetime.datetime(2019, 1, 1, 0, 0, 1)
    user.transitioningToStatus = "transition"

    # profile
    user.profile = UserProfile()
    user.profile.login = "test@lyft.com"
    user.profile.email = "test@lyft.com"
    user.profile.lastName = "LastName"
    user.profile.firstName = "firstName"

    return user
