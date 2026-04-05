def schedule_tasks(tasks: dict[str, list[str]]) -> list[str]:
    """
    Return task execution order respecting dependencies, or raise ValueError if cyclic.
    
    Args:
        tasks: A dictionary where keys are task names, and values are lists of 
               dependency task names that must be completed first.
               
    Returns:
        A list of task names in a valid topological execution order.
        
    Raises:
        ValueError: If a cyclic dependency is detected in the graph.
    """
    order = []
    visiting = set()
    visited = set()
    
    def dfs(task):
        # If the task is currently on the recursion stack, we've found a cycle
        if task in visiting:
            raise ValueError(f"Cycle detected involving {task}")
            
        # If the task has already been fully processed, skip it to avoid duplicates
        if task in visited:
            return
            
        # Mark as currently being processed
        visiting.add(task)
        
        # Traverse dependencies. Use .get() to safely handle external dependencies 
        # that are not explicitly defined as keys in the tasks dictionary.
        for dep in tasks.get(task, []):
            dfs(dep)
            
        # Move from 'visiting' to 'visited' as all dependencies are resolved
        visiting.remove(task)
        visited.add(task)
        
        # Append to order only after all dependencies have been appended
        order.append(task)
        
    # Initiate DFS for every task defined in the graph
    for task in tasks:
        dfs(task)
        
    return order