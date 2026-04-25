import pytest

from deps_file import constants


class TestDebug:
    endpoint = constants.BASE_API_PREFIX

    def test_debug_endpoint_return_500(self, client):
        with pytest.raises(ValueError):
            client.get(f"{self.endpoint}/debug/500")
