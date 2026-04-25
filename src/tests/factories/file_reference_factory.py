from uuid import uuid4

import factory
from faker import Faker

from deps_file.domain.model.file.reference import Reference, ReferenceType

__all__ = ["FileReferenceFactory"]

fake = Faker()


class FileReferenceFactory(factory.Factory):
    class Meta:
        model = Reference

    entity_type = ReferenceType.DOCUMENT
    entity_id = factory.LazyFunction(lambda: str(uuid4()))
    entity_name = factory.LazyFunction(lambda: fake.word())

    @classmethod
    def create_document_reference(cls, **kwargs):
        defaults: dict = {
            "entity_type": ReferenceType.DOCUMENT,
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def create_batch_reference(cls, **kwargs):
        defaults: dict = {
            "entity_type": ReferenceType.BATCH,
        }
        defaults.update(kwargs)
        return cls(**defaults)
