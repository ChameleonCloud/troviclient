class ProjectURN:
    def __init__(self, urn):
        self.provider, self.project_id = urn.split(":", 4)[3:]


class OwnerURN:
    def __init__(self, urn):
        self.provider, self.id = urn.split(":", 4)[3:]


class ContentsURN:
    def __init__(self, urn):
        self.provider, self.id = urn.split(":", 4)[3:]
