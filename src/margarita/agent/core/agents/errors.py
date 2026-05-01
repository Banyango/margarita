class NoModelProvidedException(Exception):
    def __init__(self):
        super().__init__("No model provided")
