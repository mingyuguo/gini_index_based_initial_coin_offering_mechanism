from loader import import_csv
from lp import bestBudgetAndError
from random import sample, uniform, seed

seed(1)
globalLog1 = 0
globalLog2 = 0

vs, bsMax = import_csv("Merged_data/_polkadot_Merged.csv")
numberOfCoins = sum(bsMax) / min(vs)
print(f"number of coins={numberOfCoins}")
print(f"revenue of dutch auction={sum(bsMax)}")
vs = [v * numberOfCoins for v in vs]
bsMaxNew = sample(bsMax, len(vs))
vsNew = [uniform(0, min(vs)) for _ in vs]
bsMax = bsMax + bsMaxNew
vs = vs + vsNew

N, minWinner = len(vs), round(len(vs) * 0.5)
print(f"N={N}, minWinner={minWinner}")
winnerNumberTrialList = [
    round(len(vs) * 0.5),
    round(len(vs) * 0.6),
    round(len(vs) * 0.7),
    round(len(vs) * 0.8),
    round(len(vs) * 0.9),
    len(vs),
]

bsCurrent = bsMax[:]

giniCap = 0.6
derivativeRatio = (giniCap + 3) / (1 - giniCap)
cappedUpperbound = minWinner - round(
    (giniCap + (minWinner + 1) / minWinner) * minWinner / 2
)
priceStep = 1
bStep = 1


def minGini(bs, p):
    "return minGini, cap, and number of agents capped, assume sorted"
    n = len(bs)
    bs = sorted(bs)
    ys = [b / p for b in bs]
    if sum(ys) < 1:
        return 1, max(bs), 0
    else:
        sofar = 0
        cap = -1
        capped = 0
        for i in range(n):
            if ys[i] * (n - i) >= 1 - sofar:
                cap = (1 - sofar) / (n - i)
                capped = n - i
                break
            else:
                sofar += ys[i]
        if cap == -1:
            cap = max(ys)
        ys = [min(y, cap) for y in ys]
        return (
            2 * sum([(i + 1) * ys[i] for i in range(n)]) / n - (n + 1) / n,
            cap * p,
            capped,
        )


print(f"gini of dutch auction={minGini(bsMax, min(vs))}")

# return -1 or price
def priceSupport(bs, priceLow=priceStep):
    if minGini(bs, priceLow)[0] > giniCap:
        return -1
    priceHigh = sum(bs)
    while priceHigh - priceLow > priceStep:
        priceMid = (priceHigh + priceLow) / 2
        if minGini(bs, priceMid)[0] > giniCap:
            priceHigh = priceMid
        else:
            priceLow = priceMid
    return priceLow


def optimalPrice():
    priceLow = priceStep
    priceHigh = sum(bsMax)
    while priceHigh - priceLow > priceStep:
        priceMid = (priceHigh + priceLow) / 2
        print("calculating optimal price:", priceLow, priceMid, priceHigh)
        bs = []
        for i in range(N):
            if vs[i] >= priceMid:
                bs.append(bsMax[i])
        bs = sorted(bs)
        priceSupported = False
        for wn in winnerNumberTrialList:
            if len(bs) < wn:
                continue
            bsSeg = bs[-wn:]
            if minGini(bsSeg, priceMid)[0] <= giniCap:
                priceSupported = True
                break
        if priceSupported:
            priceLow = priceMid
        else:
            priceHigh = priceMid
    return priceLow


op = optimalPrice()
print(f"optimal price={op}")
# initialize the equilibrium process
for i in range(N):
    if vs[i] >= op:
        bsCurrent[i] = bsMax[i]
    else:
        bsCurrent[i] = 0


def budgetPrice(bs, priceLow=priceStep):
    # this makes sense only when all winner numbers are ok
    # bs = sorted(filter(lambda b: b > 0, bs))
    bs = sorted(bs)
    assert len(bs) >= minWinner
    bestWinnerNumber = -1
    bestPriceSofar = priceLow
    for wn in winnerNumberTrialList:
        if wn > len(bs):
            continue
        p = priceSupport(bs[-wn:], priceLow=bestPriceSofar)
        # p not -1 and big enough
        if p > bestPriceSofar:
            bestWinnerNumber = wn
            bestPriceSofar = p
        if p == bestPriceSofar and wn > bestWinnerNumber:
            bestWinnerNumber = wn
    assert bestWinnerNumber != -1
    return bestPriceSofar, bestWinnerNumber


def getRank(i):
    rank = 0
    for j in range(N):
        if j == i:
            continue
        if bsCurrent[j] > bsCurrent[i] or (bsCurrent[j] == bsCurrent[i] and j < i):
            rank += 1
    return rank + 1


currentPrice = -1
currentWinnerNumber = -1
currentCap = -1
currentCapped = -1
tailPrice = -1
tailWinnerNumber = -1


def updateCurrentAndTailPrices():
    global currentPrice
    global currentWinnerNumber
    global currentCap
    global currentCapped
    global tailPrice
    global tailWinnerNumber
    tailPrice, tailWinnerNumber = budgetPrice(sorted(bsCurrent)[:-1])
    currentPrice, currentWinnerNumber = budgetPrice(bsCurrent, priceLow=tailPrice)
    _, currentCap, currentCapped = minGini(bsCurrent, currentPrice)


def budgetSequence(i):
    oldBudget = bsCurrent[i]

    if bsCurrent[i] == bsMax[i]:
        maxOutPrice, maxOutWinnerNumber = currentPrice, currentWinnerNumber
    else:
        bsCurrent[i] = bsMax[i]
        maxOutPrice, maxOutWinnerNumber = budgetPrice(bsCurrent, priceLow=currentPrice)

    _, cap, capped = minGini(bsCurrent, maxOutPrice)
    if maxOutWinnerNumber >= getRank(i):
        maxB = min(bsMax[i], cap)
    else:
        return False

    allowedCutSizes = [20, 10, 5, 1]
    for cutSize in allowedCutSizes:
        bs = []
        ps = []
        delta = maxB / cutSize
        bsCurrent[i] = delta
        p, nw = budgetPrice(bsCurrent, priceLow=tailPrice)
        if nw < getRank(i):
            continue
        if cutSize == 1:
            assert nw >= getRank(i)

        for k in range(cutSize + 1):
            bsCurrent[i] = delta * k
            p, nw = budgetPrice(bsCurrent, priceLow=tailPrice)
            bs.append(delta * k)
            ps.append(p)
        break

    bb, log1, butil, log2 = bestBudgetAndError(vs[i], bsMax[i], bs, ps)
    global globalLog1
    global globalLog2
    globalLog1 = max(globalLog1, log1)
    globalLog2 = max(globalLog2, log2)
    if (bb == bs[-1] and oldBudget > bb) or abs(bb - oldBudget) < bStep:
        bsCurrent[i] = oldBudget
        return False
    bsCurrent[i] = bb
    updateCurrentAndTailPrices()
    print(f"price change for {i} with max budget {bsMax[i]}. {oldBudget}=>{bb}")
    # if butil > 0:
    #     print(
    #         f"price change for {i} with max budget {bsMax[i]}. {oldBudget}=>{bb} with error {error} and util ratio {error/butil}"
    #     )
    # else:
    #     print(
    #         f"price change for {i} with max budget {bsMax[i]}. {oldBudget}=>{bb} with error {error} and util ratio inf"
    #     )
    return True


updateCurrentAndTailPrices()
for iterRound in range(1, 10):
    dontBuy = 0
    buyAll = 0
    changed = False
    globalLog1 = 0
    globalLog2 = 0

    for i in range(N):
        if i % 100 == 0:
            print(f"working on {i}")
        if vs[i] <= tailPrice and bsCurrent[i] == 0:
            dontBuy += 1
            continue
        if (
            bsCurrent[i] >= min(currentCap, bsMax[i])
            and vs[i]
            / currentPrice
            * (1 - derivativeRatio * min(currentCap, bsMax[i]) / currentPrice)
            >= 1
        ):
            buyAll += 1
            continue
        changedRes = budgetSequence(i)
        if not changed and changedRes:
            changed = True
    print(f"{N}={dontBuy}+{buyAll}+{N-dontBuy-buyAll}")
    print(f"entering round {iterRound+1}")
    print(currentPrice, op, minGini(bsCurrent, currentPrice), cappedUpperbound)
    print(globalLog1, globalLog2)
    if not changed:
        break
