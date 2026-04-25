from uuid import uuid4

import factory

from deps_file.domain.model import ProcessingParams, WorkflowParamsDict


class ProcessingParamsFactory(factory.Factory):
    class Meta:
        model = ProcessingParams

    group_id = factory.LazyFunction(lambda: str(uuid4()))
    splitting_enabled = True
    classification_enabled = True
    workflow_params = factory.LazyFunction(
        lambda: WorkflowParamsDict(
            document_type_id=str(uuid4()),
            parsing_features=[],
            needs_unifier=False,
            needs_extraction=False,
            assigned_to_me=False,
            llm_type=None,
            engine=None,
            language=None,
            metadata={},
        )
    )

    @classmethod
    def minimal(cls, **kwargs):
        defaults = {
            "group_id": None,
            "splitting_enabled": False,
            "classification_enabled": False,
            "workflow_params": WorkflowParamsDict(
                document_type_id=None,
                parsing_features=[],
                needs_unifier=False,
                needs_extraction=False,
                assigned_to_me=False,
                llm_type=None,
                engine=None,
                language=None,
                metadata={},
            ),
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def create_processing_params(cls, **kwargs):
        return cls(**kwargs)
