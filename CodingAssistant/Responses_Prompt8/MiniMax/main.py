def schedule_tasks(tasks: dict[str, list[str]]) -> list[str]:
    """
    Return task execution order respecting dependencies, or raise ValueError if cyclic.

    Performs a topological sort using depth-first search (DFS). The function handles:
    - Tasks with dependencies listed in the tasks dict
    - External dependencies (tasks listed as deps but not as keys) - assumed to have no dependencies
    - Cycle detection (raises ValueError for cycles including self-dependencies)

    Args:
        tasks: Dictionary mapping task names to lists of their dependencies.

    Returns:
        List of task names in valid execution order (each task appears after all its dependencies).

    Raises:
        ValueError: If a cycle is detected in the dependency graph.
    """
    order = []

    # Track nodes currently being processed (on the recursion stack)
    # Used to detect cycles - if we encounter a node in this set, we have a cycle
    visiting = set()

    # Track nodes that have been fully processed
    # Used to avoid reprocessing nodes that were already visited
    visited = set()

    def dfs(task):
        # Cycle detection: if task is currently on the recursion stack,
        # we've found a back edge which indicates a cycle
        if task in visiting:
            raise ValueError(f"Cycle detected involving {task}")

        # Already fully processed - skip
        if task in visited:
            return

        # Mark as currently being processed
        visiting.add(task)

        # Process all dependencies first
        if task in tasks:
            for dep in tasks[task]:
                dfs(dep)

        # Mark as fully processed
        visiting.remove(task)
        visited.add(task)

        # Add to order after dependencies (post-order)
        # This ensures dependencies appear before dependents
        order.append(task)

    # Process all tasks in the dictionary
    for task in tasks:
        dfs(task)

    return order


# Run tests
if __name__ == "__main__":
    # Simple linear dependency
    result = schedule_tasks({"c": ["b"], "b": ["a"], "a": []})
    assert result.index("a") < result.index("b") < result.index("c")
    assert set(result) == {"a", "b", "c"}
    print("✓ Simple linear dependency passed")

    # Independent tasks — all should appear
    result = schedule_tasks({"a": [], "b": [], "c": []})
    assert set(result) == {"a", "b", "c"}
    print("✓ Independent tasks passed")

    # Diamond dependency
    result = schedule_tasks({"d": ["b", "c"], "b": ["a"], "c": ["a"], "a": []})
    assert result.index("a") < result.index("b")
    assert result.index("a") < result.index("c")
    assert result.index("b") < result.index("d")
    assert result.index("c") < result.index("d")
    print("✓ Diamond dependency passed")

    # External dependencies (not keys in dict)
    result = schedule_tasks({"b": ["a"]})
    assert result.index("a") < result.index("b")
    assert set(result) == {"a", "b"}
    print("✓ External dependencies passed")

    # Single task, no deps
    assert schedule_tasks({"a": []}) == ["a"]
    print("✓ Single task passed")

    # Empty input
    assert schedule_tasks({}) == []
    print("✓ Empty input passed")

    # Cycle detection
    try:
        schedule_tasks({"a": ["b"], "b": ["a"]})
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    print("✓ Cycle detection (a↔b) passed")

    try:
        schedule_tasks({"a": ["b"], "b": ["c"], "c": ["a"]})
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    print("✓ Cycle detection (a→b→c→a) passed")

    # Self-dependency
    try:
        schedule_tasks({"a": ["a"]})
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    print("✓ Self-dependency detection passed")

    # Complex: multiple roots, shared deps
    result = schedule_tasks({
        "e": ["c", "d"],
        "d": ["b"],
        "c": ["a", "b"],
        "b": [],
        "a": [],
    })
    assert result.index("a") < result.index("c")
    assert result.index("b") < result.index("c")
    assert result.index("b") < result.index("d")
    assert result.index("c") < result.index("e")
    assert result.index("d") < result.index("e")
    assert set(result) == {"a", "b", "c", "d", "e"}
    print("✓ Complex: multiple roots, shared deps passed")

    print("\n✓ All tests passed!")
