def run_loop(agent, max_iterations=100):
    for i in range(max_iterations):
        print("STEP", i, flush=True)
        log_events = agent.get_background_logs()
        for event in log_events:
            print(event, flush=True)
        action = agent.get_next_action()
        if action.action == 'finish':
            print("Done!", flush=True)
            break
        print(action, flush=True)
        print("---", flush=True)
        out = agent.maybe_perform_latest_action()
        print(out, flush=True)
        print("==============", flush=True)



