def schedule_tasks(tasks: dict[str, list[str]]) -> list[str]:
    """Return task execution order respecting dependencies, or raise ValueError if cyclic.
    
    Tasks are given as a dict mapping task name to its list of dependencies.
    Tasks not in the dict but listed as dependencies are assumed to have no dependencies.
    The returned order guarantees every task appears after all of its dependencies.
    """
    order = []
    visited = set()      # Fully processed tasks
    visiting = set()     # Tasks currently in the DFS path (for cycle detection)
    
    # Collect all tasks including external dependencies
    all_tasks = set(tasks.keys())
    for deps in tasks.values():
        all_tasks.update(deps)
    
    def dfs(task):
        if task in visiting:
            raise ValueError(f"Cycle detected involving {task}")
        if task in visited:
            return  # Already fully processed, skip
        visiting.add(task)
        for dep in tasks.get(task, []):
            dfs(dep)
        visiting.remove(task)
        visited.add(task)
        order.append(task)
    
    for task in all_tasks:
        dfs(task)
    
    return order