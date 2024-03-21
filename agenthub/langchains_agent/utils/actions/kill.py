def kill(id, agent):
    if id < 0 or id >= len(agent.background_commands):
        raise ValueError('Invalid command id to kill')
    agent.background_commands[id].kill()
    agent.background_commands.pop(id)
    return "Background command %d killed" % id

