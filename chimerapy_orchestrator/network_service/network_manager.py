import chimerapy as cp


class NetworkManager(cp.Manager):
    def __init__(self, *args, **kwargs):
        kwargs["enable_api"] = True
        super().__init__(*args, **kwargs)
