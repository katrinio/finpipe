class GmailOAuth:
    @classmethod
    def build_authorization_url(cls) -> str:
        return "https://accounts.google.com/o/oauth2/auth?..."

    # @classmethod
    # def exchange_code(cls, code: str):
    #     raise NotImplementedError("Not implemented")
