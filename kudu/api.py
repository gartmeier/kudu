from datetime import datetime

import requests

BASE_URL = "https://api.pitcher.com/"


class APISession(requests.Session):
    def request(self, method, url, **kwargs):
        response =  super().request(method, BASE_URL + url, **kwargs)
        response.raise_for_status()
        return response.json()

    def authenticate(self, username, password):
        auth = self.post(
            "auth/user/",
            json={
                "username": username,
                "password": password,
            },
        )
        self.set_token(auth["token"])

    def set_token(self, token):
        self.headers.update({"Authorization": "Token %s" % (token,)})

    def get_file(self, file_id):
        return self.get('files/%d/' % file_id)

    def touch_file(self, file_id):
        return self.patch("files/%d/" % file_id, json={"creationTime": datetime.utcnow().isoformat()})

    def get_upload_url(self, file_id):
        return self.get("files/%d/upload-url/" % file_id)

    def get_download_url(self, file_id):
        return self.get("files/%d/download-url/" % file_id)


api = APISession()
