import pandas as pd
import glob
import os

os.system("ls -la /home/rtikes/Blockchain-Distributed-IDS/data/cicids2017/")
csv_files = glob.glob("/home/rtikes/Blockchain-Distributed-IDS/data/cicids2017/*.csv")

df_list = [pd.read_csv(f) for f in csv_files]
df = pd.concat(df_list, ignore_index=True)

df.to_csv("/home/rtikes/Blockchain-Distributed-IDS/data/CICIDS2017_full.csv", index=False)

os.system("ls -la /home/rtikes/Blockchain-Distributed-IDS/data/")

