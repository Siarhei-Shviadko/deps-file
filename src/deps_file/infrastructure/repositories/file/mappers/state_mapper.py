from typing import Any

from deps_file.domain.model import ErrorCode, State


class StateMapper:
    @staticmethod
    def to_dict(state: State) -> dict[str, Any]:
        return {
            "status": state.status,
            "error_message": state.error_message,
            "error_code": state.error_code and state.error_code.value,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> State:
        return State(
            status=data["status"],
            error_message=data.get("error_message"),
            error_code=(error_code := data.get("error_code")) and ErrorCode(error_code),
        )
