from pulp import LpProblem, LpVariable, LpMinimize, GLPK, value


def toConcave(x):
    """Turn x to x', ensuring x'_i-1 + x'_i+1 <= 2 x'_i, return error and x'"""
    n = len(x)

    testFailed = False
    for i in range(1, n - 1):
        if x[i - 1] + x[i + 1] > 2 * x[i]:
            testFailed = True
    if not testFailed:
        return 0, x

    prob = LpProblem("toConcave", LpMinimize)

    # >= 0
    xprime = [LpVariable("xprime" + str(i), 0) for i in range(n)]
    epsilon = LpVariable("epsilon", 0)

    prob += epsilon, "Minimize epsilon"

    # assume ascending
    for i in range(n - 1):
        prob += xprime[i] <= xprime[i + 1]
    for i in range(n):
        prob += xprime[i] >= x[i] - epsilon
        prob += xprime[i] <= x[i] + epsilon
    for i in range(1, n - 1):
        prob += xprime[i - 1] + xprime[i + 1] <= 2 * xprime[i]

    prob.solve(GLPK())
    # print("Status:", LpStatus[prob.status])
    # for v in prob.variables():
    #     print(v.name, "=", v.varValue)
    # print("Epsilon = ", value(prob.objective))

    # makes sense to force ascending
    xprimeValues = sorted(
        v.varValue for v in prob.variables() if v.name.startswith("xprime")
    )
    # assertion to ensure lp solution found
    assert len(xprimeValues) == n
    return value(prob.objective), xprimeValues


def bestBudgetAndError(v, bMax, bs, ps):
    """ bs[0] is min budget to get allocated (0?), bs[-1] is the max budget allowed, either by capping or by budget constraint of the agent """
    n = len(bs)
    bps = [bs[i] / ps[i] for i in range(n)]

    assert len(bs) == len(ps)
    assert bs[0] == 0
    for i in range(n - 1):
        assert bps[i] <= bps[i + 1], f"{bps}"
        assert bs[i] <= bs[i + 1]
        assert ps[i] <= ps[i + 1]

    errorLP, bpsConcave = toConcave(bps)

    maxError2 = 0
    for i in range(n - 1):
        maxError2 = max(
            bs[i + 1] * (ps[i + 1] - ps[i]) / (ps[i] * ps[i + 1]), maxError2
        )

    bestBudget = 0
    bestUtil = 0
    for i in range(n):
        util = bpsConcave[i] * v - bs[i]
        if util > bestUtil:
            bestUtil = util
            bestBudget = bs[i]

    print(
        f"errorLP={errorLP}, maxError2={maxError2}, total={errorLP+maxError2}, v={v}, prod={2*(errorLP+maxError2)*v}, bpsMaxratio={2*(errorLP+maxError2)*v/bMax}"
    )
    print(bs)
    print(ps)
    print(bpsConcave)
    print()
    return (
        bestBudget,
        v * 2 * (errorLP + maxError2),
        bestUtil,
        2 * (errorLP + maxError2) * v / bMax,
    )
