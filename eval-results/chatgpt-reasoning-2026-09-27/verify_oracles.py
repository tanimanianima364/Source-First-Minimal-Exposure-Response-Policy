"""Independent finite checks for the two closed-world reasoning fixtures. Stdlib only."""
from itertools import combinations, product
import json

NAMES = 'ABCDEFGH'
COST = dict(zip(NAMES, (2, 3, 4, 5, 2, 4, 3, 5)))
VALUES = dict(zip(NAMES, ((6, 2, 1), (2, 7, 1), (1, 2, 8), (5, 5, 3),
                         (4, 1, 4), (3, 6, 6), (8, 2, 4), (2, 8, 6))))
BONUS = {'AB': (2, 0, 1), 'DE': (0, 3, 2), 'BG': (1, 2, 0)}


def score(items, state):
    return sum(VALUES[x][state] for x in items) + sum(
        v[state] for pair, v in BONUS.items() if set(pair) <= items)


def allowed(first, added, budget):
    items = set(first + added)
    return (sum(COST[x] for x in items) <= budget
            and not set('EH') <= items and not set('CF') <= items
            and ('G' not in items or 'B' in first))


def solve(budget):
    rows, policies, fixed = {}, [], []
    for pair in combinations(NAMES, 2):
        first = ''.join(pair)
        if sum(COST[x] for x in first) > 7 or not allowed(first, '', budget):
            continue
        options = [''] + [x for x in NAMES if x not in first and allowed(first, x, budget)]
        maxima = [max(score(set(first + x), s) for x in options) for s in range(3)]
        rows[first] = {'state_maxima': maxima, 'upper_bound': min(maxima)}
        # Separate full contingent-policy enumeration verifies the min-of-max formula.
        for policy in product(options, repeat=3):
            outcomes = [score(set(first + policy[s]), s) for s in range(3)]
            policies.append((min(outcomes), first, policy, outcomes))
        for x in options:
            outcomes = [score(set(first + x), s) for s in range(3)]
            fixed.append((min(outcomes), first, x, outcomes))
    best = max(x[0] for x in policies)
    assert best == max(r['upper_bound'] for r in rows.values())
    best_fixed = max(x[0] for x in fixed)
    return {'rows': rows, 'adaptive_optimum': best,
            'optimal_first_pairs': sorted({x[1] for x in policies if x[0] == best}),
            'witnesses': [next(x for x in policies if x[0] == best and x[1] == p)
                          for p in sorted({x[1] for x in policies if x[0] == best})],
            'fixed_optimum': best_fixed,
            'fixed_witness': next(x for x in fixed if x[0] == best_fixed)}


def interleavings(lengths, prefix=()):
    if not any(lengths):
        yield prefix
    for i, left in enumerate(lengths):
        if left:
            remaining = list(lengths)
            remaining[i] -= 1
            yield from interleavings(tuple(remaining), prefix + (i,))


def scan(serialized, modulus):
    # Thread 0/1: writer(1)/(2); thread 2: one reader attempt.
    count = failures = 0
    minimum_completed = None
    witness = None
    for order in interleavings((4, 4, 4)):
        if serialized and max(i for i, t in enumerate(order) if t == 0) > min(
                i for i, t in enumerate(order) if t == 1):
            continue
        count += 1
        pc, state, reads, completed, trace = [0, 0, 0], [0, 0, 0], [], 0, []
        for thread in order:
            step = pc[thread]
            pc[thread] += 1
            if thread < 2:
                if step in (0, 3):
                    state[0] += 1
                    if modulus:
                        state[0] %= modulus
                else:
                    state[step] = thread + 1
                completed += step == 3
                trace.append(f'W{thread + 1}.{step + 1}: seq,x,y={state}')
            else:
                value = state[(0, 1, 2, 0)[step]]
                reads.append(value)
                trace.append(f'R{step + 1}={value}')
                if step == 3:
                    a, p, q, b = reads
                    if a == b and a % 2 == 0 and p != q:
                        failures += 1
                        if minimum_completed is None or completed < minimum_completed:
                            minimum_completed, witness = completed, trace[:]
                    break
    return {'schedules': count, 'mixed_return_schedules': failures,
            'minimum_completed_writers': minimum_completed, 'witness': witness}


if __name__ == '__main__':
    ten, eleven = solve(10), solve(11)
    assert (ten['adaptive_optimum'], ten['optimal_first_pairs']) == (13, ['BE', 'BG'])
    assert ten['fixed_optimum'] == 12
    assert (eleven['adaptive_optimum'], eleven['optimal_first_pairs']) == (15, ['DE'])
    wrapped, parallel, repaired = scan(True, 4), scan(False, None), scan(True, None)
    assert wrapped['minimum_completed_writers'] == 2
    assert parallel['minimum_completed_writers'] == 0
    assert repaired['mixed_return_schedules'] == 0
    print(json.dumps({'budget10': ten, 'budget11': eleven, 'serialized_mod4': wrapped,
                      'parallel_unbounded': parallel, 'serialized_unbounded': repaired},
                     ensure_ascii=False, indent=2))
