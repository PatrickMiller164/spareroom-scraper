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

from dataclasses import dataclass, field, fields

@dataclass
class Room:
    # Simple default value
    price: float = field(
        default=0.0,
        metadata={
            'include_in_output': True,
            'use_in_score': True,
            'good_range': (0, 10000),
            'weight': 0.3
        }
    )

eg = Room(price=4)

for f in fields(eg):
    print(f.name)
    print(getattr(eg, f.name))
    print(f.metadata['good_range'])