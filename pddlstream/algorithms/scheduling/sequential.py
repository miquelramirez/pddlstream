from pddlstream.algorithms.downward import task_from_domain_problem, get_problem, TOTAL_COST, sas_from_pddl
from pddlstream.algorithms.search import solve_from_task, abstrips_solve_from_task
from pddlstream.algorithms.scheduling.simultaneous import extract_function_results, add_stream_actions
from pddlstream.algorithms.scheduling.utils import evaluations_from_stream_plan, get_results_from_head
from pddlstream.language.conversion import obj_from_pddl
from pddlstream.language.stream import Stream
from pddlstream.utils import find_unique, INF, MockSet


# TODO: interpolate between all the scheduling options

def simplify_actions(opt_evaluations, action_plan, task, actions, unit_costs):
    # TODO: add ordering constraints to simplify the optimization
    import pddl
    import instantiate

    fluent_facts = MockSet()
    init_facts = set()
    type_to_objects = instantiate.get_objects_by_type(task.objects, task.types)
    results_from_head = get_results_from_head(opt_evaluations)

    action_from_name = {}
    function_plan = set()
    for i, (name, args) in enumerate(action_plan):
        action = find_unique(lambda a: a.name == name, actions)
        assert (len(action.parameters) == len(args))
        # parameters = action.parameters[:action.num_external_parameters]
        var_mapping = {p.name: a for p, a in zip(action.parameters, args)}
        new_name = '{}-{}'.format(name, i)
        new_parameters = action.parameters[len(args):]
        new_preconditions = []
        action.precondition.instantiate(var_mapping, init_facts, fluent_facts, new_preconditions)
        new_effects = []
        for eff in action.effects:
            eff.instantiate(var_mapping, init_facts, fluent_facts, type_to_objects, new_effects)
        new_effects = [pddl.Effect([], pddl.Conjunction(conditions), effect)
                       for conditions, effect in new_effects]
        cost = pddl.Increase(fluent=pddl.PrimitiveNumericExpression(symbol=TOTAL_COST, args=[]),
                             expression=pddl.NumericConstant(1))
        # cost = None
        task.actions.append(pddl.Action(new_name, new_parameters, len(new_parameters),
                                        pddl.Conjunction(new_preconditions), new_effects, cost))
        action_from_name[new_name] = (name, map(obj_from_pddl, args))
        if not unit_costs:
            function_result = extract_function_results(results_from_head, action, args)
            if function_result is not None:
                function_plan.add(function_result)
    return action_from_name, list(function_plan)


def sequential_stream_plan(evaluations, goal_expression, domain, stream_results,
                           negated, effort_weight, unit_costs=True, debug=False, **kwargs):
    # Intuitively, actions have infinitely more weight than streams
    if negated:
        raise NotImplementedError(negated)
    for result in stream_results:
        if isinstance(result.external, Stream) and result.external.is_fluent():
            raise NotImplementedError('Fluents are not supported')

    # TODO: compute preimage and make that the goal instead
    opt_evaluations = evaluations_from_stream_plan(evaluations, stream_results)
    opt_task = task_from_domain_problem(domain, get_problem(opt_evaluations, goal_expression, domain, unit_costs))
    action_plan, action_cost = abstrips_solve_from_task(sas_from_pddl(opt_task, debug=debug), debug=debug, **kwargs)
    if action_plan is None:
        return None, action_cost

    actions = domain.actions[:]
    domain.actions[:] = []
    stream_domain, stream_result_from_name = add_stream_actions(domain, stream_results) # TODO: effort_weight
    domain.actions.extend(actions)
    stream_task = task_from_domain_problem(stream_domain, get_problem(evaluations, goal_expression, stream_domain, unit_costs))
    action_from_name, function_plan = simplify_actions(opt_evaluations, action_plan, stream_task, actions, unit_costs)

    # TODO: lmcut?
    combined_plan, _ = solve_from_task(sas_from_pddl(opt_task, debug=debug),
                                       planner=kwargs.get('planner', 'ff-astar'),
                                       debug=debug, **kwargs)
    if combined_plan is None:
        return None, INF

    stream_plan, action_plan = [], []
    for name, args in combined_plan:
        if name in stream_result_from_name:
            stream_plan.append(stream_result_from_name[name])
        else:
            action_plan.append(action_from_name[name])
    combined_plan = stream_plan + function_plan + action_plan
    return combined_plan, action_cost
