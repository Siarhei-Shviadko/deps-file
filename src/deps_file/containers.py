from typing import Any, Dict, Optional, Type, Union

from dependency_injector import containers, providers, resources
from deps_asb import ASBClient, ASBConsumer, ASBProducer
from deps_kafka import KafkaClient, KafkaConsumer, KafkaProducer
from deps_message_flow import MessagingDriverEnum
from deps_message_flow.commands.producer import CommandProducer
from deps_message_flow.events.publisher import DomainEventPublisher
from deps_message_flow.messaging.consumer import IMessageConsumer
from deps_message_flow.messaging.producer import IMessageProducer
from deps_message_flow.sagas.orchestration import (
    SagaCommandProducer,
    SagaDataMapping,
    SagaInstanceFactory,
    SagaManagerFactory,
)
from deps_object_storage import ObjectStorage, make_object_storage
from deps_rabbitmq import RabbitMQClient, RabbitMQConsumer, RabbitMQProducer

from deps_file.application import (
    CommandGroupService,
    CommandUserService,
    QueryUserService,
    SagaFileService,
)
from deps_file.application.file import (
    CommandFileService,
    IBatchProxy,
    IDocumentProxy,
    QueryFileService,
)
from deps_file.application.group import IGroupProxy
from deps_file.constants import PROJECT_NAME
from deps_file.domain.model import ICommandFileRepository, IQueryUserRepository
from deps_file.domain.model.file import IQueryFileRepository
from deps_file.extras import DatabaseSession
from deps_file.infrastructure.access_management import user
from deps_file.infrastructure.proxies import (
    BatchProxy,
    DocumentProxy,
    InternalGroupProxy,
)
from deps_file.infrastructure.repositories import (
    QueryFileRepository,
    QueryUserRepository,
    UoWCommandFileRepository,
)
from deps_file.infrastructure.repositories.saga_instance import SagaInstanceRepository
from deps_file.infrastructure.unit_of_work import (
    AbstractUnitOfWork,
    SqlAlchemyUnitOfWork,
)
from deps_file.messaging import ClassifySaga, ProcessingSaga, SplitSaga
from deps_file.messaging.dispatcher import make_message_dispatcher
from deps_file.messaging.orchestration import make_saga_data_mapping

MessagingClient = Union[ASBClient, KafkaClient, RabbitMQClient]


class MessageBrokerResource(resources.Resource):
    def init(
        self,
        driver_type: str,
        expected_driver: str,
        client: Type[MessagingClient],
        message_connection_string: str,
        **kwargs: dict[str, Any],
    ) -> Optional[MessagingClient]:
        return client(message_connection_string, **kwargs) if driver_type == expected_driver else None

    def shutdown(self, resource: Optional[MessagingClient]) -> None:
        if resource:
            resource.close()


class MessageBrokers(containers.DeclarativeContainer):
    config = providers.Configuration()
    messaging_driver_settings = providers.Dependency(instance_of=object)

    broker_client: providers.Provider[MessagingClient] = providers.Selector(
        config.messaging_driver,
        asb=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.ASB.value,
            expected_driver=config.messaging_driver,
            client=ASBClient,
            message_connection_string=config.message_broker_connection_string,
            asb_settings=messaging_driver_settings,
        ),
        kafka=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.KAFKA.value,
            expected_driver=config.messaging_driver,
            client=KafkaClient,
            message_connection_string=config.message_broker_connection_string,
            settings=messaging_driver_settings,
        ),
        rabbitmq=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.RABBITMQ.value,
            expected_driver=config.messaging_driver,
            client=RabbitMQClient,
            message_connection_string=config.message_broker_connection_string,
            settings=messaging_driver_settings,
        ),
    )


class Messaging(containers.DeclarativeContainer):
    config = providers.Configuration()
    message_brokers = providers.DependenciesContainer()

    producer: providers.Provider[IMessageProducer] = providers.Selector(
        config.messaging_driver,
        asb=providers.Singleton(
            ASBProducer,
            client=message_brokers.broker_client,
            topic_name=config.messaging_driver_settings.topic_name,
        ),
        kafka=providers.Singleton(
            KafkaProducer,
            client=message_brokers.broker_client,
        ),
        rabbitmq=providers.Singleton(
            RabbitMQProducer,
            client=message_brokers.broker_client,
        ),
    )
    consumer: providers.Provider[IMessageConsumer] = providers.Selector(
        config.messaging_driver,
        asb=providers.Singleton(
            ASBConsumer,
            client=message_brokers.broker_client,
            topic_name=config.messaging_driver_settings.topic_name,
            custom_subscription_name=PROJECT_NAME,
        ),
        kafka=providers.Singleton(
            KafkaConsumer,
            client=message_brokers.broker_client,
        ),
        rabbitmq=providers.Singleton(
            RabbitMQConsumer,
            client=message_brokers.broker_client,
        ),
    )


class Core(containers.DeclarativeContainer):
    config = providers.Configuration()
    build_info: providers.Provider[Dict] = providers.Dict(
        {
            "build_tag": config.info.tag,
            "build_date": config.info.date,
            "commit_hash": config.info.hash,
        },
    )


class Datasources(containers.DeclarativeContainer):
    config = providers.Configuration()

    postgres_session: providers.Provider[DatabaseSession] = providers.Singleton(
        DatabaseSession,
        config.user,
        config.password,
        config.host,
        config.port,
        config.db,
        config.dialect,
        config.driver,
        {},
        config.require_secure_transport,
        pool_size=config.pool_size,
    )


class Repositories(containers.DeclarativeContainer):
    config = providers.Configuration()
    datasources = providers.DependenciesContainer()

    query_user: providers.Singleton[IQueryUserRepository] = providers.Singleton(
        QueryUserRepository,
        database=datasources.postgres_session,
    )

    query_file: providers.Singleton[IQueryFileRepository] = providers.Singleton(
        QueryFileRepository,
        database=datasources.postgres_session,
    )

    command_file: providers.Singleton[ICommandFileRepository] = providers.Singleton(
        UoWCommandFileRepository,
        connection=datasources.postgres_session,
    )

    saga_instance: providers.Provider[SagaInstanceRepository] = providers.Singleton(
        SagaInstanceRepository,
        datasources.postgres_session,
    )


class ExternalServices(containers.DeclarativeContainer):
    config = providers.Configuration()

    group: providers.Provider[IGroupProxy] = providers.Singleton(
        InternalGroupProxy,
        base_url=config.group.url,
        timeout=config.group.proxy_timeout,
        ssl_verify=config.ssl_verify,
    )

    object_storage: providers.Provider[ObjectStorage] = providers.Singleton(make_object_storage)

    document: providers.Provider[IDocumentProxy] = providers.Singleton(
        DocumentProxy,
        base_url=config.document.url,
        timeout=config.document.proxy_timeout,
        ssl_verify=config.ssl_verify,
    )

    batch: providers.Provider[IBatchProxy] = providers.Singleton(
        BatchProxy,
        base_url=config.batch.url,
        timeout=config.batch.proxy_timeout,
        ssl_verify=config.ssl_verify,
    )


class Containers(containers.DeclarativeContainer):
    config = providers.Configuration()
    messaging_driver_settings = providers.Dependency(instance_of=object)
    current_user_tenant = providers.Callable(lambda: user.get()["organisation"])

    external_services: providers.Container[ExternalServices] = providers.Container(
        ExternalServices,
        config=config,
    )

    datasources: providers.Container[Datasources] = providers.Container(
        Datasources,
        config=config.database,
    )

    repositories: providers.Container[Repositories] = providers.Container(
        Repositories,
        config=config,
        datasources=datasources,
    )

    core: providers.Container[Core] = providers.Container(Core, config=config)
    message_brokers: providers.Container[MessageBrokers] = providers.Container(
        MessageBrokers,
        config=config,
        messaging_driver_settings=messaging_driver_settings,
    )

    messaging: providers.Container[Messaging] = providers.Container(
        Messaging,
        config=config,
        message_brokers=message_brokers,
    )

    command_producer: providers.Singleton[CommandProducer] = providers.Singleton(
        CommandProducer,
        messaging.producer,
    )

    domain_event_publisher: providers.Singleton[DomainEventPublisher] = providers.Singleton(
        DomainEventPublisher,
        messaging.producer,
    )

    message_dispatcher: providers.Singleton[IMessageConsumer] = providers.Singleton(
        make_message_dispatcher,
        messaging.consumer,
        messaging.producer,
    )

    saga_command_producer: providers.Singleton[CommandProducer] = providers.Singleton(
        SagaCommandProducer,
        command_producer,
    )

    saga_data_mapping: providers.Singleton[SagaDataMapping] = providers.Singleton(
        make_saga_data_mapping,
    )

    saga_manager_factory: providers.Singleton[SagaManagerFactory] = providers.Singleton(
        SagaManagerFactory,
        repositories.saga_instance,
        command_producer,
        messaging.consumer,
        saga_command_producer,
        saga_data_mapping,
    )

    unit_of_work: providers.Singleton[AbstractUnitOfWork] = providers.Singleton(
        SqlAlchemyUnitOfWork,
        database_session=datasources.postgres_session,
    )

    query_user_service: providers.Singleton[QueryUserService] = providers.Singleton(
        QueryUserService,
        query_user_repository=repositories.query_user,
    )

    command_user_service: providers.Singleton[CommandUserService] = providers.Singleton(
        CommandUserService,
        unit_of_work=unit_of_work,
        domain_event_publisher=domain_event_publisher,
    )

    query_file_service: providers.Singleton[QueryFileService] = providers.Singleton(
        QueryFileService,
        query_file_repository=repositories.query_file,
    )

    command_file_service: providers.Singleton[CommandFileService] = providers.Singleton(
        CommandFileService,
        object_storage=external_services.object_storage,
        unit_of_work=unit_of_work,
        domain_event_publisher=domain_event_publisher,
        command_producer=command_producer,
        document_proxy=external_services.document,
        batch_proxy=external_services.batch,
    )

    sagas = providers.List(
        providers.Singleton(
            ProcessingSaga,
            command_file_service=command_file_service,
        ),
        providers.Singleton(
            ClassifySaga,
            command_file_service=command_file_service,
        ),
        providers.Singleton(
            SplitSaga,
            command_file_service=command_file_service,
        ),
    )

    saga_instance_factory: providers.Singleton[SagaManagerFactory] = providers.Singleton(
        SagaInstanceFactory,
        saga_manager_factory,
        sagas,
    )

    saga_file_service: providers.Singleton[SagaFileService] = providers.Singleton(
        SagaFileService,
        saga_instance_factory=saga_instance_factory,
        sagas=sagas,
    )

    command_group_service: providers.Singleton[CommandGroupService] = providers.Singleton(
        CommandGroupService,
        unit_of_work=unit_of_work,
        command_producer=command_producer,
        domain_event_publisher=domain_event_publisher,
        group_proxy=external_services.group,
    )
