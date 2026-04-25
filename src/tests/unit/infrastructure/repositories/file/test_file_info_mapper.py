from datetime import datetime

from deps_file.infrastructure.repositories.file.mappers import file_info_mapper


def test_details_labels_and_processing_defaults():
    row = {
        "file_id": "f1",
        "tenant_id": "t1",
        "name": "doc.pdf",
        "path": "/u/doc.pdf",
        "state": {"status": "PROCESSING"},
        "processing_params": None,
        "labels": ["alpha", None, "beta"],
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }

    info = file_info_mapper.FileInfoMapper.to_file_details_info(row)

    assert info["labels"] == ["alpha", "beta"]
    assert info["processing_params"] == {}


def test_parse_rows_to_files_info_builds_result_set_counts(mocker):
    now = datetime.utcnow()
    # Using actual dictionaries instead of Mock objects for simpler testing
    rows = [
        {
            "file_id": "f1",
            "tenant_id": "t1",
            "name": "a.pdf",
            "path": "/u/a.pdf",
            "state": {"status": "PROCESSING"},
            "processing_params": {},
            "labels": ["alpha"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "file_id": "f2",
            "tenant_id": "t1",
            "name": "b.pdf",
            "path": "/u/b.pdf",
            "state": {"status": "COMPLETED"},
            "processing_params": {},
            "labels": None,
            "created_at": now,
            "updated_at": now,
        },
    ]

    info = file_info_mapper.FileInfoMapper.parse_rows_to_files_info(rows, total=10)
    assert info["result_set"]["count"] == 2
    assert info["result_set"]["limit"] >= 2
    assert info["result_set"]["total"] == 10
