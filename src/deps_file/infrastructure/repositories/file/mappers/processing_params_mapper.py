from typing import Any, Optional

from deps_file.domain.model import ProcessingParams


class ProcessingParamsMapper:
    @staticmethod
    def to_dict(params: Optional[ProcessingParams]) -> Optional[dict[str, Any]]:
        if not params:
            return None

        return {
            "group_id": params.group_id() if params.group_id else None,
            "splitting_enabled": params.splitting_enabled,
            "classification_enabled": params.classification_enabled,
            "workflow_params": params.workflow_params,
        }

    @staticmethod
    def from_dict(data: Optional[dict[str, Any]]) -> Optional[ProcessingParams]:
        if not data:
            return None

        return ProcessingParams(
            group_id=data.get("group_id"),
            splitting_enabled=data.get("splitting_enabled", False),
            classification_enabled=data.get("classification_enabled", False),
            workflow_params=data.get("workflow_params", {}),
        )
