def validate_command_list(raw_cmd):
    if isinstance(raw_cmd, str):
        return raw_cmd.split()
    return raw_cmd
