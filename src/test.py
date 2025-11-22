def normalise_x(min, max, x):
    return 1 - ((x - min) / (max - min))

for i in [0, 10, 20, 30, 40, 50, 60, 70, 80]:
    min = 20
    max = 60
    try:
        res = normalise_x(20, 60, i)
        print(min, max, i, res)

    except ZeroDivisionError:
        print(f"{i} causes ZeroDivisionError")