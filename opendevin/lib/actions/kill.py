def kill(id, command_mgr):
    if id < 0 or id >= len(command_mgr.background_commands):
        raise ValueError('Invalid command id to kill')
    command_mgr.background_commands[id].kill()
    command_mgr.background_commands.pop(id)
    return "Background command %d killed" % id


