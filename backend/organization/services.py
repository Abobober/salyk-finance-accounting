from organization.models import OrganizationProfile


def get_or_create_organization_profile(user):
    profile, _ = OrganizationProfile.objects.get_or_create(user=user)
    return profile
