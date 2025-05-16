class AppState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.token = None
            cls._instance.user = None
        return cls._instance

    def set_token(self, token):
        self.token = token

    def set_user(self, user):
        self.user = user
