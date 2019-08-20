import datetime

from okta.models.user.User import User


def create_test_user():
    user = User()

    user.id = "userid"
    user.activated = True
    user.created = datetime.now
    user.activated = datetime.now
    user.statusChanged = datetime.now
    user.lastLogin = datetime.now
    user.lastUpdated = datetime.now
    user.passwordChanged = datetime.now
    user.transitioningToStatus = "transition"

    # profile
    user.profile.login = "test@lyft.com"
    user.profile.email = "test@lyft.com"
    user.profile.secondEmail = "test2@lyft.com"
    user.profile.lastName = "LastName"
    user.profile.firstName = "firstName"
    user.profile.mobilePhone = "000-000-0000"

    return user
