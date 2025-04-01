from rest_framework_simplejwt.tokens import RefreshToken

def generate_tokens_for_user(user):
    """
    Генерирует access и refresh токены для пользователя.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh), str(refresh.access_token)