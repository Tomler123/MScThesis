def schedule_tasks(tasks: dict[str, list[str]]) -> list[str]:
    """Return a topological execution order for tasks.

    Each task appears after all of its dependencies. Dependencies that are
    mentioned but are not keys in `tasks` are treated as leaf tasks with no
    dependencies. Raises ValueError if the dependency graph contains a cycle.
    """
    order: list[str] = []
    visiting: set[str] = set()   # currently being processed
    visited: set[str] = set()    # fully processed

    def dfs(task: str) -> None:
        if task in visited:
            return
        if task in visiting:
            raise ValueError(f"Cycle detected involving {task}")

        visiting.add(task)

        for dep in tasks.get(task, []):
            dfs(dep)

        visiting.remove(task)
        visited.add(task)
        order.append(task)

    for task in tasks:
        dfs(task)

    return order