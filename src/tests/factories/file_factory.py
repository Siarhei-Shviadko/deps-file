from datetime import datetime, timezone
from uuid import uuid4

import factory

from deps_file.domain.model.file import File, FileId
from deps_file.domain.model.shared import TenantId

from .file_processing_params_factory import ProcessingParamsFactory
from .file_state_factory import StateFactory

__all__ = ["FileFactory"]


class FileFactory(factory.Factory):
    class Meta:
        model = File

    id_ = factory.LazyFunction(lambda: FileId().value)
    tenant_id = factory.LazyFunction(lambda: TenantId().value)
    name = factory.Sequence(lambda n: f"test_file_{n}.pdf")
    path = factory.Sequence(lambda n: f"/uploads/tenant_1/test_file_{n}.pdf")
    state = factory.SubFactory(StateFactory)
    processing_params = factory.SubFactory(ProcessingParamsFactory)
    labels = factory.LazyAttribute(lambda o: [uuid4().hex for _ in range(5)])
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    events = factory.List([])

    @classmethod
    def create_with_minimal_data(cls, **kwargs):
        defaults = {
            "name": "minimal_file.pdf",
            "path": "/uploads/minimal_file.pdf",
            "state": StateFactory.processing(),
            "processing_params": ProcessingParamsFactory.minimal(),
            "created_at": None,
            "updated_at": None,
            "labels": None,
            "events": [],
        }
        defaults.update(kwargs)

        return cls(**defaults)

    @classmethod
    def create_for_splitting(
        cls, group_id=None, splitting_enabled=True, classification_enabled=False, workflow_params=None, **kwargs
    ):
        processing_params = cls.create_processing_params(
            group_id=group_id,
            splitting_enabled=splitting_enabled,
            classification_enabled=classification_enabled,
            workflow_params=workflow_params,
        )
        defaults = {
            "processing_params": processing_params,
        }
        defaults.update(kwargs)
        return cls.create_file(defaults)

    @classmethod
    def create_for_classification(
        cls, group_id=None, splitting_enabled=False, classification_enabled=True, workflow_params=None, **kwargs
    ):
        processing_params = cls.create_processing_params(
            group_id=group_id,
            splitting_enabled=splitting_enabled,
            classification_enabled=classification_enabled,
            workflow_params=workflow_params,
        )
        defaults = {
            "processing_params": processing_params,
        }
        defaults.update(kwargs)
        return cls.create_file(defaults)

    @classmethod
    def create_for_processing(
        cls, group_id=None, splitting_enabled=False, classification_enabled=False, workflow_params=None, **kwargs
    ):
        processing_params = cls.create_processing_params(
            group_id=group_id,
            splitting_enabled=splitting_enabled,
            classification_enabled=classification_enabled,
            workflow_params=workflow_params,
        )
        defaults = {
            "processing_params": processing_params,
        }
        defaults.update(kwargs)
        return cls.create_file(defaults)

    @classmethod
    def create_processing_params(
        cls,
        group_id=None,
        splitting_enabled=False,
        classification_enabled=False,
        workflow_params=None,
    ):
        processing_params = {
            "splitting_enabled": splitting_enabled,
            "classification_enabled": classification_enabled,
        }
        if group_id is not None:
            processing_params["group_id"] = group_id
        if workflow_params is not None:
            processing_params["workflow_params"] = workflow_params

        return ProcessingParamsFactory.create_processing_params(**processing_params)

    @classmethod
    def create_file(cls, defaults):
        file = cls(**defaults)
        file.generate_pipeline_command()
        return file
