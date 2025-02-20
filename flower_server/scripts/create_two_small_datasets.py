import pandas as pd
import os

DATA_PATH = "/home/rtikes/Blockchain-Distributed-IDS/data/CICIDS2017_full.csv"
df = pd.read_csv(DATA_PATH)

df.columns = df.columns.str.strip()

benign_alpha = df[df["Label"] == "BENIGN"].sample(n=50000, random_state=42)
benign_beta = df[df["Label"] == "BENIGN"].drop(benign_alpha.index).sample(n=50000, random_state=42)

attacks_alpha = df[df["Label"] != "BENIGN"].sample(n=50000, random_state=42)
attacks_beta = df[df["Label"] != "BENIGN"].drop(attacks_alpha.index).sample(n=50000, random_state=42)

df_alpha = pd.concat([benign_alpha, attacks_alpha]).sample(frac=1, random_state=42)
df_beta = pd.concat([benign_beta, attacks_beta]).sample(frac=1, random_state=42)

output_path_alpha = "/home/rtikes/Blockchain-Distributed-IDS/raspberry_pi/node-alpha/data/CICIDS2017_alpha.csv"
output_path_beta = "/home/rtikes/Blockchain-Distributed-IDS/raspberry_pi/node-beta/data/CICIDS2017_beta.csv"

df_alpha.to_csv(output_path_alpha, index=False)
df_beta.to_csv(output_path_beta, index=False)

os.system("ls -la /home/rtikes/Blockchain-Distributed-IDS/raspberry_pi/node-alpha/data/")
os.system("ls -la /home/rtikes/Blockchain-Distributed-IDS/raspberry_pi/node-beta/data/")

