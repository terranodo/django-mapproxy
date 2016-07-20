from guardian.utils import get_anonymous_user


class GuardianAuthenticationMiddleware(object):
    def process_request(self, request):
        if request.user.is_anonymous():
            request.user = get_anonymous_user()
