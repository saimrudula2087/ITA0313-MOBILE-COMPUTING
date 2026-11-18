import math

def erlang_b(channels, traffic):
    b = 1.0
    for m in range(1, channels + 1):
        b = traffic * b / (m + traffic * b)
    return b

def erlang_capacity(channels, target=0.02):
    low, high = 0.0, channels * 3.0
    for _ in range(100):
        mid = (low + high) / 2
        if erlang_b(channels, mid) > target:
            high = mid
        else:
            low = mid
    return (low + high) / 2

def hex_area(radius):
    return (3 * math.sqrt(3) / 2) * radius ** 2

def cell_count(area, radius):
    return math.ceil(area / hex_area(radius))

def sir_db(cluster, n, interferers=6):
    return 10 * math.log10((3 * cluster) ** (n / 2) / interferers)

def borrow_channel(preferred_free, neighbour_free, sir_safe):
    if preferred_free > 0:
        return "ACCEPT: preferred channel"
    if neighbour_free > 0 and sir_safe:
        return "ACCEPT: borrowed channel"
    return "BLOCK: no safe channel"

def split_rounds(initial_capacity, demand):
    if demand <= initial_capacity:
        return 0
    return math.ceil(math.log(demand / initial_capacity, 4))

def main():
    S, N, beta = 336, 7, 0.02
    m = S // N
    A = erlang_capacity(m, beta)
    print("MOBILE COMPUTING - CELLULAR NETWORK PLANNER")
    print("=" * 48)
    print("TASK 1: CHANNEL ALLOCATION")
    print("Total channels:", S)
    print("Reuse cluster size:", N)
    print("Channels per cell:", m)
    print("\nTASK 2: HEXAGONAL REUSE")
    print("For i=2, j=1, N =", 2*2 + 2*1 + 1*1)
    print("Reuse ratio Q =", round(math.sqrt(3*N), 3))
    print("\nTASK 3: ERLANG-B CAPACITY")
    print("Offered traffic at 2% blocking:", round(A, 3), "Erlangs/cell")
    print("Blocking verification:", round(erlang_b(m, A), 4))
    print("Carried traffic:", round(A*(1-beta), 3), "Erlangs/cell")
    print("Subscriber equivalent:", round(A/0.025))
    print("\nTASK 4: SIR RESULTS")
    for n in [2.5, 3.0, 3.5, 4.0]:
        print("n =", n, "SIR =", round(sir_db(N,n), 2), "dB")
    print("\nTASK 5: CELL COUNT AND CAPACITY")
    for R in [0.50, 0.25]:
        c = cell_count(12, R)
        total = c*A
        print("R =", R, "km | cells =", c, "| capacity =", round(total,2),
              "Erlangs | subscribers =", round(total/0.025))
    print("\nTASK 6: SUBSCRIBER TRAFFIC")
    for users in [1000, 10000, 20000, 100000]:
        print(users, "subscribers ->", users*0.025, "Erlangs")
    print("\nTASK 7: CHANNEL BORROWING")
    print(borrow_channel(1,0,True))
    print(borrow_channel(0,1,True))
    print(borrow_channel(0,1,False))
    print("\nTASK 8: CELL SPLITTING")
    macro = cell_count(12,0.50)*A
    demand = 100000*0.025
    k = split_rounds(macro,demand)
    print("Initial macro capacity:", round(macro,2), "Erlangs")
    print("Demand:", demand, "Erlangs")
    print("Ideal split rounds:", k)
    print("Capacity after splitting:", round(macro*4**k,2), "Erlangs")
    print("\nTASK 9: STADIUM EVENT")
    event = 25000*0.05
    cells = math.ceil(event/A)
    print("Event traffic:", event, "Erlangs")
    print("Required cell-equivalents:", cells)
    print("Estimated capacity:", round(cells*A,2), "Erlangs")
    print("\nTASK 10: RECOMMENDATION")
    print("Use N=7, 48 channels/cell, 0.50 km macro radius,")
    print("selective microcells, sectorisation and safe channel borrowing.")

if __name__ == "__main__":
    main()
