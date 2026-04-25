from typing import List

from deps_file.domain.model import FileFactory, WorkflowParamsDict


def seed_files_with_dates(unit_of_work, tenant_id: str):
    files: List = []
    with unit_of_work:
        for i in range(4):
            f = FileFactory.create_for_processing(
                tenant_id=tenant_id,
                name=f"doc_{i}.pdf",
                path=f"/uploads/doc_{i}.pdf",
                group_id=None,
                workflow_params=WorkflowParamsDict(document_type_id=None),
            )
            unit_of_work.files.save(f)
            files.append(f)
        unit_of_work.commit()
    return files
