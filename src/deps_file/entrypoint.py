import logging
import os
from typing import Awaitable, Callable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response

from deps_file import api, constants, messaging
from deps_file.api.error_handlers import json_file_error_handler, register_error_handler
from deps_file.containers import Containers
from deps_file.domain.exceptions import AuthError
from deps_file.infrastructure.access_management import user
from deps_file.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_containers(settings: Settings) -> Containers:
    containers = Containers(messaging_driver_settings=settings.messaging_driver_settings)
    settings_dict = settings.model_dump()
    containers.config.from_dict(settings_dict)
    containers.init_resources()
    containers.wire(
        packages=[api, messaging],
    )

    containers.message_brokers.broker_client().user_context = user

    containers.core.wire(
        modules=[api.endpoints.service_info],
    )
    containers.datasources.wire(
        modules=[api.endpoints.healthcheck],
    )

    return containers


def create_fastapi() -> FastAPI:
    settings = Settings()
    containers: Containers = init_containers(settings)
    _base_service_init(containers)

    fastapi_app = FastAPI(
        title=constants.PROJECT_NAME,
        version=containers.config.version(),
        docs_url=f"{constants.V1_API_PREFIX}{constants.SWAGGER_DOC_URL}"
        if containers.config.documentation_enabled()
        else None,
        description=constants.DESCRIPTION,
        openapi_url=f"{constants.V1_API_PREFIX}/openapi.json" if containers.config.documentation_enabled() else None,
    )
    fastapi_app.include_router(api.debug_router, prefix=constants.BASE_API_PREFIX)
    fastapi_app.include_router(api.healthcheck_router, prefix=constants.BASE_API_PREFIX)
    fastapi_app.include_router(api.service_info_router, prefix=constants.BASE_API_PREFIX)
    fastapi_app.include_router(api.files_router, prefix=constants.BASE_API_PREFIX)
    fastapi_app.containers = containers

    register_error_handler(fastapi_app)
    register_auth(fastapi_app)

    if containers.config.instrumentation_enabled():
        from deps_observability_instrumentation import (  # noqa: WPS433
            instrument_fast_api,
        )

        instrument_fast_api(fastapi_app)

    return fastapi_app


def register_auth(app: FastAPI):
    api.add_auth_to_openapi(app)

    @app.middleware("http")
    async def handle_authorization(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        try:
            api.auth.set_user_from_token(request)
        except AuthError as err:
            return json_file_error_handler(err, err.status_code)
        return await call_next(request)


def run_api():
    use_web_concurrency = "WEB_CONCURRENCY" in os.environ
    env = os.getenv("ENV", "prod")
    options = {
        "host": "0.0.0.0",  # noqa: S104
        "port": 8000,
        "log_level": os.getenv("LOG_LEVEL", "debug").lower(),
        "workers": int(os.getenv("WEB_CONCURRENCY")) if use_web_concurrency else 3,
        "reload": env == "development",
        "debug": env == "development",
    }

    uvicorn.run("deps_file.entrypoint:create_fastapi", **options)


def run_message_dispatcher() -> None:
    settings = Settings()
    containers: Containers = init_containers(settings)
    _base_service_init(containers)

    # Subscribes for sagas reply channels
    containers.saga_instance_factory()

    containers.command_group_service().initialize()

    dispatcher = containers.message_dispatcher()
    dispatcher.start_consuming()


def _base_service_init(containers: Containers) -> None:
    if containers.config.instrumentation_enabled():
        logger.info("Instrumentation enabled.")
        from deps_observability_instrumentation import (  # noqa: WPS433
            instrument_messaging,
            setup_instrumentation,
        )

        setup_instrumentation()
        instrument_messaging(containers.messaging.producer(), containers.messaging.consumer())
