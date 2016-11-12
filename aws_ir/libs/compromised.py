class CompromisedMetadata(object):
    def __init__(
        self,
        compromised_object_inventory,
        case_number,
        type_of_compromise
    ):

        self.inventory = compromised_object_inventory
        self.case_number = case_number
        self.compromise_type = type_of_compromise

    def data(self):
        metadata = self.inventory
        metadata['case_number'] = self.case_number
        metadata['compromise_type'] = self.compromise_type
        return metadata
