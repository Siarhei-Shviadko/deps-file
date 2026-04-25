from deps_file.messaging.handlers import split_file_handler


def test_split_file_handler__passes_all_parameters(
    mock_saga_file_service,
    split_file_cm,
    split_file_command,
    tenant_id,
):
    split_file_handler(split_file_cm)

    mock_saga_file_service.split_file.assert_called_once_with(
        assigned_to_me=split_file_command.assigned_to_me,
        classification_enabled=split_file_command.classification_enabled,
        document_type_id=split_file_command.document_type_id,
        engine=split_file_command.engine,
        file_id=split_file_command.file_id,
        file_name=split_file_command.file_name,
        file_path=split_file_command.path,
        group_id=split_file_command.group_id,
        language=split_file_command.language,
        llm_type=split_file_command.llm_type,
        metadata=split_file_command.metadata,
        needs_extraction=split_file_command.needs_extraction,
        needs_unifier=split_file_command.needs_unifier,
        parsing_features=split_file_command.parsing_features,
        tenant_id=tenant_id(),
    )
