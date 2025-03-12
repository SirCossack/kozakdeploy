from social_core.pipeline.user import USER_FIELDS
from social_core.backends.twitch import TwitchOAuth2

def append_UID_to_database_fields(strategy, details, request, backend, user=None, *args, **kwargs):
    """
    Just appends 'UID' to a list of kwargs that gets passed to login.models.AppUserManager.create_user().

    """
    global USER_FIELDS
    request.session['uid'] = kwargs['uid']
    USER_FIELDS.append('uid')
    return

def check_wtf_is_wrong(strategy, uid, details, request, backend, user=None, *args, **kwargs):
    """  print(strategy)
    print(backend)
    print("REQUEST  ", request)
    print("DETAILS ", details)
    print("user  ", user)
    print("args  ", args)
    print("kwargs  ", kwargs)
    print(backend.name, uid)
    print(backend.strategy.storage.user.get_social_auth(backend.name, uid))
    print(backend.strategy.storage.user)
    print(backend.strategy.storage)
    print(backend.strategy)"""

    return