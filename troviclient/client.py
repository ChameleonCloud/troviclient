import requests
from urllib.parse import urljoin, urlparse, urlencode
from keycloak.realm import KeycloakRealm

from .exceptions import TroviException

TROVI_API_BASE_URL = "https://trovi-dev.chameleoncloud.org"


class TroviClient():
    def __init__(
            self, keycloak_url, keycloak_realm, oidc_client_id,
            oidc_client_secret, admin=False, base_url=TROVI_API_BASE_URL,
            scopes=None):
        self.base_url = base_url
        self.admin = admin
        self.keycloak_url = keycloak_url
        self.keycloak_realm = keycloak_realm
        self.oidc_client_id = oidc_client_id
        self.oidc_client_secret = oidc_client_secret
        if scopes is None:
            self.scopes = ["artifacts:read"]
        else:
            self.scopes = scopes

    def _get_token(self):
        realm = KeycloakRealm(
            server_url=self.keycloak_url, realm_name=self.keycloak_realm)
        openid = realm.open_id_connect(
            client_id=self.oidc_client_id,
            client_secret=self.oidc_client_secret,
        )
        creds = openid.client_credentials()
        scopes = self.scopes
        if self.admin:
            scopes.append("trovi:admin")
        res = requests.post(
            urljoin(self.base_url, "/token/"),
            json={
                "grant_type": "token_exchange",
                "subject_token": creds["access_token"],
                "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
                "scope": " ".join(scopes),
            },
        )
        self._check_status(res, requests.codes.created)
        return res.json()

    def _url_with_token(self, path, query=None):
        if not query:
            query = {}
        query["access_token"] = self._get_token()["access_token"]
        return urljoin(self.base_url, f"{path}?{urlencode(query)}")

    def _check_status(self, response, code):
        if code and response.status_code != code:
            try:
                response_json = response.json()
                detail = response_json.get(
                    "detail",
                    response_json.get("error_description", response.text)
                )
            except AttributeError:
                detail = response.text
            except requests.exceptions.JSONDecodeError:
                if response.status_code == 500:
                    detail = ""
                else:
                    detail = response.text
            request = response.request
            request_path = urlparse(request.url).path
            message = (
                f"{request.method} {request_path} {response.status_code} "
                f"returned, expected {code}: {detail}"
            )
            raise TroviException(response.status_code, message)

    def _get(self, path, query=None, status=requests.codes.ok):
        res = requests.get(
            self._url_with_token(path, query=query)
        )
        self._check_status(res, status)
        return res

    def _post(
            self, path, json_data, query=None, status=requests.codes.created):
        res = requests.post(
            self._url_with_token(path, query=query), json=json_data
        )
        self._check_status(res, status)
        return res

    def _patch(self, path, json_data, query=None, status=requests.codes.ok):
        res = requests.post(
            self._url_with_token(path, query=query), json=json_data
        )
        self._check_status(res, status)
        return res

    def _delete(self, path, query=None, status=requests.codes.no_content):
        res = requests.delete(
            self._url_with_token(path, query=query)
        )
        self._check_status(res, status)
        return res

    def _put(self, path, query=None, status=requests.codes.no_content):
        res = requests.put(
            self._url_with_token(path, query=query)
        )
        self._check_status(res, status)
        return res

    def list_artifacts(self, sort_by="updated_at"):
        res = self._get(
            "/artifacts/", query=dict(sort_by=sort_by))
        return res.json()["artifacts"]

    def create_artifact(self, artifact, force=False):
        query = {}
        if force:
            query["force"] = True
        res = self._post(
            "/artifacts/", artifact, query=query)
        return res.json()

    def get_artifact(self, artifact_id, sharing_key=None):
        query = {}
        if sharing_key:
            query["sharing_key"] = sharing_key
        res = self._get(f"/artifacts/{artifact_id}/", query=query)
        return res.json()

    def patch_artifact(self, artifact_id, patches, force=False):
        json_data = {"patch": patches}
        query = {}
        if force:
            query["force"] = True
        res = self._patch(
            f"/artifacts/{artifact_id}/", json_data, query=query)
        return res.json()

    def list_tags(self):
        res = self._get("/meta/tags/")
        return res.json()["tags"]

    def create_tag(self, tag):
        json_data = {"tag": tag}
        res = self._post("/meta/tags/", json_data)
        return res.json()["tag"]

    def create_version(
        self, artifact_id, contents_urn, links=None, created_at=None
    ):
        json_data = {"contents": {"urn": contents_urn}}
        if links:
            json_data["links"] = links
        query = None
        if created_at:
            json_data["created_at"] = created_at
            query["force"] = True
        res = self._post(
            f"/artifacts/{artifact_id}/versions/",
            json=json_data, query=query
        )
        return res.json()

    def migrate_version(self, artifact_id, version_slug, backend="zenodo"):
        res = self._post(
            f"/artifacts/{artifact_id}/versions/{version_slug}/migration/",
            json={"backend": "zenodo"},
            status=requests.codes.accepted
        )
        return res.json()

    def delete_version(self, artifact_id, slug):
        self._delete(f"/artifacts/{artifact_id}/versions/{slug}/")

    def increment_metric_count(
        self, artifact_id, version_slug, origin_token,
        metric="access_count", amount=1
    ):
        query = {
            "metric": metric,
            "amount": amount,
            "origin": origin_token,
        }
        self._put(
            f"/artifacts/{artifact_id}/versions/{version_slug}/metrics/",
            query=query,
        )

    def get_contents(self, urn, sharing_key=None):
        query = {"urn": urn}
        if sharing_key:
            query["sharing_key"] = sharing_key
        res = self._get("/contents/", query=query)
        return res.json()

    def set_linked_chameleon_project(
            self, artifact_id, charge_code, token=None):
        new_urn = f"urn:trovi:project:chameleon:{charge_code}"
        artifact = self.get_artifact(artifact_id)
        project_indices = [
            i
            for i, project in enumerate(artifact["linked_projects"])
            if project.split(":", 4)[3] == "chameleon"
        ]
        patches = []
        # Replace index if it exists
        if project_indices:
            patches.append(
                {
                    "op": "replace",
                    "path": f"/linked_projects/{project_indices[0]}",
                    "value": new_urn,
                }
            )
        else:
            patches.append(
                {"op": "add", "path": "/linked_projects/-", "value": new_urn})
        self.patch_artifact(artifact_id, patches)
