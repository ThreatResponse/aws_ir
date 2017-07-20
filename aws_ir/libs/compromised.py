class CompromisedMetadata(object):
    def __init__(
        self,
        compromised_object_inventory,
        case_number,
        type_of_compromise,
        examiner_cidr_range='0.0.0.0/0'
    ):

        self.inventory = compromised_object_inventory
        self.case_number = case_number
        self.examiner_cidr_range = examiner_cidr_range
        self.compromise_type = type_of_compromise

    def data(self):
        metadata = self.inventory
        metadata['case_number'] = self.case_number
        metadata['compromise_type'] = self.compromise_type
        metadata['public_ip_address'] = self.inventory.get('public_ip_address', None)
        metadata['platform'] = self.inventory['platform']
        metadata['examiner_cidr_range'] = self.examiner_cidr_range
        return metadata
