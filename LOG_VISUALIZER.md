The log visualizer allows you to visualize the history of each agent session. To produce the log, simply remember to hit "Clear" after the end of each session, whereupon the log of that session will be saved to the folder `frontend_log`.

After that, run `python my_log_visualizer.py` to start the Gradio frontend for the visualization, where you can select the log file to visualize.

The visualization will not only include the MCTS planning search tree, but also the state, active strategy, and action for steps where the agent does not replan. Feel free to take advantage of this to debug any reasoning errors (e.g., not recognizing the task is done).
