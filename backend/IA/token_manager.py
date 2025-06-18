import boto3
import json
import tempfile
from datetime import datetime

class TokenManager:
    def __init__(self, bucket="qubo-token-usage", key="tokens.json", max_requests=50):
        self.bucket = bucket
        self.key = key
        self.max_requests = max_requests
        self.s3 = boto3.client("s3")
        self.tokens = self._load_tokens()

    def _download_from_s3(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.s3.download_file(self.bucket, self.key, temp_file.name)
        return temp_file.name

    def _upload_to_s3(self, file_path):
        self.s3.upload_file(file_path, self.bucket, self.key)

    def _load_tokens(self):
        file_path = self._download_from_s3()
        with open(file_path, "r") as file:
            tokens = json.load(file)

        today = datetime.now().date().isoformat()

        for token in tokens:
            if "count" not in token:
                token["count"] = 0
            if "date" not in token or token["date"] != today:
                token["count"] = 0
                token["date"] = today

        self._save_tokens(tokens)
        return tokens

    def _save_tokens(self, tokens=None):
        tokens = tokens or self.tokens
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as file:
            json.dump(tokens, file, indent=2)
            temp_path = file.name
        self._upload_to_s3(temp_path)

    def get_token(self):
        for token in self.tokens:
            if token["count"] < self.max_requests:
                token["count"] += 1
                self._save_tokens()
                print(f"🔁 Usando token terminado en: {token['token'][-4:]}, usados: {token['count']}")
                return token["token"]

        raise Exception("🚫 Todos los tokens alcanzaron el límite diario.")
