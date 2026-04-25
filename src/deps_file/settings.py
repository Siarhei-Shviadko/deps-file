from typing import Any

from deps_asb import ASBSettings
from deps_kafka import KafkaSettings
from deps_message_flow import MessagingDriverEnum
from deps_rabbitmq import RabbitMQTLSSettings
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from deps_file.extras import DatabaseSettings, ServiceInfoSettings


class GroupProxySettings(BaseSettings):
    url: str = Field(..., validation_alias="GROUP_URL")
    proxy_timeout: int = 60

    model_config = {"env_prefix": "GROUP_"}


class DocumentProxySettings(BaseSettings):
    url: str = Field(..., validation_alias="DOCUMENT_URL")
    proxy_timeout: int = 60

    model_config = {"env_prefix": "DOCUMENT_"}


class BatchProxySettings(BaseSettings):
    url: str = Field(..., validation_alias="FILES_BATCH_URL")
    proxy_timeout: int = 60

    model_config = {"env_prefix": "FILES_BATCH_"}


class Settings(BaseSettings):
    env: str = "development"
    version: str = "1.0"

    logger_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    info: ServiceInfoSettings = ServiceInfoSettings()
    database: DatabaseSettings = DatabaseSettings()

    messaging_driver: MessagingDriverEnum = Field(
        default=MessagingDriverEnum.RABBITMQ,
        validation_alias="MESSAGING_DRIVER",
    )
    messaging_driver_settings: Any = Field(default=None, validation_alias="MESSAGING_DRIVER_SETTINGS")
    message_broker_connection_string: str

    documentation_enabled: bool = True
    instrumentation_enabled: bool = False

    group: GroupProxySettings = GroupProxySettings()
    document: DocumentProxySettings = DocumentProxySettings()
    batch: BatchProxySettings = BatchProxySettings()

    model_config = SettingsConfigDict(use_enum_values=True)

    @classmethod
    @field_validator("messaging_driver_settings")
    def validate_messaging_driver_settings(cls, v, info):  # noqa: N805
        messaging_driver = info.data.get("messaging_driver")
        if not messaging_driver:
            raise ValueError("Invalid messaging driver")

        driver = MessagingDriverEnum(messaging_driver)
        if driver == MessagingDriverEnum.ASB:
            return ASBSettings()
        elif driver == MessagingDriverEnum.KAFKA:
            return KafkaSettings()
        elif driver == MessagingDriverEnum.RABBITMQ:
            return RabbitMQTLSSettings().model_dump()  # TODO: use BaseSettings

        raise ValueError(f"Driver {driver} is not implemented")
