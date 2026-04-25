from deps_file import constants


class TestServiceInfo:
    endpoint = constants.BASE_API_PREFIX + "/service-info"

    def test_version(self, client):
        response = client.get(f"{self.endpoint}/version")

        assert response.status_code == 200
