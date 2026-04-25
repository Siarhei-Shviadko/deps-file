import dataclasses

from deps_message_flow.commands.common import Command

from deps_file.domain.model.file.commands import ClassifyFileDomain


def test_classify_file_command__contains_required_fields(classify_file_command, test_file_1):
    assert classify_file_command.file_id == str(test_file_1.id())
    assert classify_file_command.file_name == test_file_1.name
    assert classify_file_command.path == test_file_1.path
    assert classify_file_command.group_id == test_file_1.processing_params.group_id()
    assert classify_file_command.engine == test_file_1.processing_params.workflow_params.get("engine")
    assert classify_file_command.language == test_file_1.processing_params.workflow_params.get("language")
    assert classify_file_command.parsing_features == test_file_1.processing_params.workflow_params.get(
        "parsing_features"
    )
    assert classify_file_command.llm_type == test_file_1.processing_params.workflow_params.get("llm_type")
    assert classify_file_command.needs_unifier == test_file_1.processing_params.workflow_params.get(
        "needs_unifier", False
    )
    assert classify_file_command.needs_extraction == test_file_1.processing_params.workflow_params.get(
        "needs_extraction", False
    )
    assert classify_file_command.metadata == test_file_1.processing_params.workflow_params.get("metadata")


def test_classify_file_command__is_dataclass():
    assert dataclasses.is_dataclass(ClassifyFileDomain)


def test_classify_file_command__inherits_from_command():
    command = ClassifyFileDomain(file_id="test", file_name="test.pdf", path="test", group_id="test")

    assert isinstance(command, Command)


def test_classify_file_command__equality(test_file_1):
    command1 = ClassifyFileDomain(
        file_id=str(test_file_1.id()),
        file_name=test_file_1.name,
        path=test_file_1.path,
        group_id=test_file_1.processing_params.group_id(),
        engine="advanced",
    )

    command2 = ClassifyFileDomain(
        file_id=str(test_file_1.id()),
        file_name=test_file_1.name,
        path=test_file_1.path,
        group_id=test_file_1.processing_params.group_id(),
        engine="advanced",
    )

    assert command1 == command2


def test_classify_file_command__inequality_different_data(fake):
    command1 = ClassifyFileDomain(
        file_id=fake.uuid4(),
        file_name="file1.pdf",
        path="/path1.pdf",
        group_id=fake.uuid4(),
        engine="basic",
    )

    command2 = ClassifyFileDomain(
        file_id=fake.uuid4(),
        file_name="file2.pdf",
        path="/path2.pdf",
        group_id=fake.uuid4(),
        engine="advanced",
    )

    assert command1 != command2


def test_classify_file_command__all_optional_fields_can_be_set(fake):
    command = ClassifyFileDomain(
        file_id=fake.uuid4(),
        file_name="complex.pdf",
        path="/storage/complex.pdf",
        group_id=fake.uuid4(),
        engine="advanced",
        language="en",
        llm_type="gpt-4",
        parsing_features=["tables", "forms"],
        needs_unifier=True,
        needs_extraction=True,
        metadata={"priority": "high", "source": "api"},
    )

    assert command.engine == "advanced"
    assert command.language == "en"
    assert command.llm_type == "gpt-4"
    assert command.parsing_features == ["tables", "forms"]
    assert command.needs_unifier is True
    assert command.needs_extraction is True
    assert command.metadata == {"priority": "high", "source": "api"}
    assert command.metadata["priority"] == "high"
    assert "tables" in command.parsing_features
