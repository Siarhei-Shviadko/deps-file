import logging

from deps_message_flow.sagas.orchestration import Saga, SagaInstanceFactory

from deps_file.messaging.orchestration import (
    ClassifySaga,
    ClassifySagaData,
    ProcessingSaga,
    ProcessingSagaData,
    SplitSaga,
    SplitSagaData,
)

__all__ = ["SagaFileService"]


class SagaFileService:
    def __init__(
        self,
        saga_instance_factory: SagaInstanceFactory,
        sagas: list[Saga],
    ) -> None:
        self._sagas = {saga.__class__: saga for saga in sagas}
        self._saga_instance_factory = saga_instance_factory

        self._logger = logging.getLogger(self.__class__.__name__)

    def process_file(
        self,
        file_id: str,
        tenant_id: str,
        files: list[str],
        parsing_features: list[str],
        engine: str | None = None,
        language: str | None = None,
    ) -> None:
        data = ProcessingSagaData(
            file_id=file_id,
            tenant_id=tenant_id,
            files=files,
            engine=engine,
            language=language,
            parsing_features=parsing_features,
        )

        si = self._saga_instance_factory.create(
            self._sagas[ProcessingSaga],
            data,
        )

        self._logger.info("Processing of file %s is started with saga %s.", file_id, si.saga_id)

    def classify_file(
        self,
        file_id: str,
        tenant_id: str,
        file_path: str,
        file_name: str,
        group_id: str,
        parsing_features: list[str],
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        needs_unifier: bool = False,
        needs_extraction: bool = False,
        assigned_to_me: bool = False,
        metadata: dict[str, str] | None = None,
    ) -> None:
        data = ClassifySagaData(
            file_id=file_id,
            tenant_id=tenant_id,
            file_path=file_path,
            file_name=file_name,
            group_id=group_id,
            parsing_features=parsing_features,
            engine=engine,
            language=language,
            llm_type=llm_type,
            needs_unifier=needs_unifier,
            needs_extraction=needs_extraction,
            assigned_to_me=assigned_to_me,
            metadata=metadata,
        )

        si = self._saga_instance_factory.create(
            self._sagas[ClassifySaga],
            data,
        )

        self._logger.info("Classification of file %s is started with saga %s.", file_id, si.saga_id)

    def split_file(
        self,
        file_id: str,
        tenant_id: str,
        file_path: str,
        file_name: str,
        group_id: str,
        document_type_id: str,
        classification_enabled: bool,
        parsing_features: list[str] | None = None,
        engine: str | None = None,
        language: str | None = None,
        llm_type: str | None = None,
        needs_unifier: bool = False,
        needs_extraction: bool = True,
        assigned_to_me: bool = False,
        metadata: dict[str, str] | None = None,
    ) -> None:
        si = self._saga_instance_factory.create(
            saga=self._sagas[SplitSaga],
            data=SplitSagaData(
                file_id=file_id,
                tenant_id=tenant_id,
                file_path=file_path,
                file_name=file_name,
                group_id=group_id,
                document_type_id=document_type_id,
                classification_enabled=classification_enabled,
                parsing_features=parsing_features,
                engine=engine,
                language=language,
                llm_type=llm_type,
                needs_unifier=needs_unifier,
                needs_extraction=needs_extraction,
                assigned_to_me=assigned_to_me,
                metadata=metadata,
            ),
        )

        self._logger.info("Splitting of file %s is started with saga %s.", file_id, si.saga_id)
