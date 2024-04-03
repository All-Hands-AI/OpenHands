from e2b import Sandbox


class E2BSandbox:
    closed = False

    def __init__(
        self,
        template: str = "base",
    ):
        self.sandbox = Sandbox(template=template)

    def execute(self):
        pass

    def close(self):
        self.sandbox.close()
