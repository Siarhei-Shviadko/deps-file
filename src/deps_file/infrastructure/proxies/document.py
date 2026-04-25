import json
from typing import Any

from deps_file.application import IDocumentProxy

from .exceptions import DocumentProxyRequestError
from .generic import GenericProxy

__all__ = ["DocumentProxy"]


class DocumentProxy(IDocumentProxy, GenericProxy):
    exception = DocumentProxyRequestError

    def __init__(self, base_url: str, timeout: int, ssl_verify: bool):
        super().__init__(base_url)
        self._timeout = timeout
        self._ssl_verify = ssl_verify

    def create_document_from_file(
        self,
        file_name: str,
        file_content: bytes,
        document_type_id: str,
        group_id: str | None = None,
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        parsing_features: list[str] | None = None,
        needs_unification: bool = True,
        needs_extraction: bool = True,
        needs_parsing: bool = False,
        assign_to_me: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        url = f"{self._base_url}/api-internal/document/documents/from-file"

        data = {
            "documentName": file_name,
            "documentType": document_type_id,
            "groupId": group_id,
            "engine": engine,
            "language": language,
            "llmType": llm_type,
            "needsUnifier": needs_unification,
            "needsExtraction": needs_extraction,
            "needsParsing": needs_parsing,
            "parsingFeatures": json.dumps(parsing_features) if parsing_features else None,
            "metadata": json.dumps(metadata) if metadata else None,
            "assignedToMe": str(assign_to_me),
        }

        data = {key: value for key, value in data.items() if value is not None}

        files = {"file": (file_name, file_content, "application/octet-stream")}

        response = self._session.post(
            url,
            data=data,
            files=files,
            timeout=self._timeout,
            verify=self._ssl_verify,
        )

        self._check_response(response)
        response_data = response.json()

        return response_data["documentId"], response_data["documentName"]
