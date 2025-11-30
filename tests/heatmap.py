import pandas as pd
import numpy as np

# Example DF
df = pd.DataFrame(
    np.random.rand(5, 4),
    index=["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"],
    columns=pd.date_range("2024-01-01", periods=4)
)

print(df)