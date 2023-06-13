from typing import Any
from typing import Dict
from typing import List

import requests


class GandiAPI:
    TIMEOUT = (600, 600)

    def __init__(self, apikey: str) -> None:
        self._base_url: str = 'https://api.gandi.net/v5/'
        self._session = requests.Session()
        self._session.headers.update(
            {
                'Authorization': f'Apikey {apikey}',
                'User-Agent': 'Cartography/0.1',
            },
        )

    def get_organizations(self) -> List[Dict[str, Any]]:
        result = []
        req = self._session.get(f'{self._base_url}/organization/organizations', timeout=self.TIMEOUT)
        req.raise_for_status()
        for org in req.json():
            if org['type'] == 'individual':
                continue
            result.append(org)
        return result

    def get_domains(self) -> List[Dict[str, Any]]:
        result = []
        # List domains
        list_req = self._session.get(f'{self._base_url}/domain/domains', timeout=self.TIMEOUT)
        list_req.raise_for_status()
        for dom in list_req.json():
            # Get domains informations
            req = self._session.get(dom['href'])
            req.raise_for_status()
            domain = req.json().copy()
            # Get records
            if 'dnssec' in domain['services']:
                req = self._session.get(f'{self._base_url}/livedns/domains/{dom["fqdn"]}/records', timeout=self.TIMEOUT)
                req.raise_for_status()
                domain['records'] = req.json()
            result.append(domain)
        return result
