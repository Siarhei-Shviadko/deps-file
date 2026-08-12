from typing import Any

from deps_file.application import BatchFileDict, IBatchProxy

from .exceptions import BatchProxyRequestError
from .generic import GenericProxy

__all__ = ["BatchProxy"]


class BatchProxy(IBatchProxy, GenericProxy):
    exception = BatchProxyRequestError

    def __init__(self, base_url: str, timeout: int, ssl_verify: bool):
        super().__init__(base_url)
        self._timeout = timeout
        self._ssl_verify = ssl_verify

    def create_batch_from_files(
        self,
        batch_name: str,
        files: list[BatchFileDict],
        source_file_id: str,
        group_id: str | None = None,
        metadata: dict | None = None,
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        parsing_features: list[str] | None = None,
    ) -> tuple[str, str]:
        url = f"{self._base_url}/api-internal/files-batch/batches/from-file"

        files_data = []
        processing_params = dict[str, Any]({})
        if engine is not None:
            processing_params["engine"] = engine
        if language is not None:
            processing_params["language"] = language
        if llm_type is not None:
            processing_params["llmType"] = llm_type
        if parsing_features is not None:
            processing_params["parsingFeatures"] = parsing_features

        for file in files:
            file_data = {
                "name": file["name"],
                "path": file["path"],
                "processingParams": processing_params,
            }

            if file.get("document_type_id") is not None:
                file_data["documentTypeId"] = file["document_type_id"]

            files_data.append(file_data)

        data = dict[str, Any]({"name": batch_name, "files": files_data, "sourceFileId": source_file_id})

        if group_id is not None:
            data["groupId"] = group_id
        if metadata is not None:
            data["metadata"] = metadata

        response = self._session.post(
            url,
            json=data,
            timeout=self._timeout,
            verify=self._ssl_verify,
        )

        self._check_response(response)
        response_data = response.json()

        return response_data["batchId"], response_data["batchName"]
