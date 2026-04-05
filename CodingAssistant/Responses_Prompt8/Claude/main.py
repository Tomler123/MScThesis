def schedule_tasks(tasks: dict[str, list[str]]) -> list[str]:
    """
    Return a valid topological execution order for the given tasks, respecting dependencies.

    Each key in `tasks` maps to a list of task names that must complete before it.
    Tasks referenced as dependencies but absent from `tasks` are treated as having
    no dependencies and are included in the output.

    Raises ValueError if a cycle is detected.
    """
    order = []
    # Three states: 0 = unvisited, 1 = in-progress, 2 = fully processed
    state = {}

    # Gather all nodes, including implicit ones from dependency lists
    all_tasks = set(tasks.keys())
    for deps in tasks.values():
        all_tasks.update(deps)

    def dfs(task):
        s = state.get(task, 0)
        if s == 1:
            raise ValueError(f"Cycle detected involving '{task}'")
        if s == 2:
            return  # Already fully processed; skip
        state[task] = 1  # Mark as in-progress
        for dep in tasks.get(task, []):
            dfs(dep)
        state[task] = 2  # Mark as fully processed
        order.append(task)

    for task in all_tasks:
        if state.get(task, 0) == 0:
            dfs(task)

    return order