import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import scipy.stats as stats

# Load and clean the data
df = pd.read_excel("CDLBO6Stats.xlsx")
df.columns = df.columns.str.strip().str.lower()

# Ensure correct data types
df["map"] = pd.to_numeric(df["map"], errors="coerce")
df["kills"] = pd.to_numeric(df["kills"], errors="coerce")
df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce")

# Main window setup
root = tk.Tk()
root.title("CDL Player Prop Statlab")
root.geometry("1200x900")
root.configure(bg="#f5f5f5")

# Style
style = ttk.Style()
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10, "bold"))
style.configure("TCombobox", font=("Segoe UI", 10))
style.configure("TLabelFrame", background="#f5f5f5", font=("Segoe UI", 10, "bold"))
style.configure("TFrame", background="#f5f5f5")

# ========== Filter Frame ==========
filter_frame = ttk.LabelFrame(root, text="Filters")
filter_frame.pack(fill='x', padx=10, pady=10)

players = df["player"].unique().tolist()
opponents = ["(All)"] + sorted(df["opponent"].dropna().unique().tolist())
majors = ["(All)"] + sorted(df["major"].dropna().unique().tolist())

selected_player = tk.StringVar(value=players[0])
selected_opp = tk.StringVar(value="(All)")
selected_major = tk.StringVar(value="(All)")
ou_line = tk.DoubleVar(value=51.5)

def on_change(*args): update_stats()
selected_player.trace_add("write", on_change)
selected_opp.trace_add("write", on_change)
selected_major.trace_add("write", on_change)

ttk.Label(filter_frame, text="Player:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
ttk.Combobox(filter_frame, textvariable=selected_player, values=players, state="readonly", width=18).grid(row=0, column=1, padx=5)

ttk.Label(filter_frame, text="O/U Line (Maps 1-3):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
ttk.Entry(filter_frame, textvariable=ou_line, width=10).grid(row=0, column=3, padx=5)

ttk.Label(filter_frame, text="Opponent:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
ttk.Combobox(filter_frame, textvariable=selected_opp, values=opponents, state="readonly", width=18).grid(row=0, column=5, padx=5)

ttk.Label(filter_frame, text="Major:").grid(row=0, column=6, padx=5, pady=5, sticky="e")
ttk.Combobox(filter_frame, textvariable=selected_major, values=majors, state="readonly", width=18).grid(row=0, column=7, padx=5)

# ========== Stats Display ==========
stats_frame = ttk.LabelFrame(root, text="Player Statistics (Maps 1-3)")
stats_frame.pack(fill='x', padx=10, pady=5)

avg_kills_var = tk.StringVar()
stdev_var = tk.StringVar()
med_kills_var = tk.StringVar()
conf_int_var = tk.StringVar()
total_kills_var = tk.StringVar()
map_count_var = tk.StringVar()
kd_var = tk.StringVar()

labels = [
    ("Avg. Kills:", avg_kills_var),
    ("St. Dev:", stdev_var),
    ("Median:", med_kills_var),
    ("95% CI:", conf_int_var),
    ("Total Kills:", total_kills_var),
    ("Map Count:", map_count_var),
    ("K/D Ratio:", kd_var),
]

for i, (label, var) in enumerate(labels):
    ttk.Label(stats_frame, text=label).grid(row=0, column=i*2, sticky="e", padx=5, pady=5)
    ttk.Label(stats_frame, textvariable=var).grid(row=0, column=i*2+1, sticky="w", padx=5, pady=5)

# ========== Graphs ==========
modes = ["Hardpoint", "Search & Destroy", "Control"]
mode_frames = {}
mode_canvases = {}

middle_frame = ttk.Frame(root)
middle_frame.pack(fill='both', expand=True, padx=10, pady=10)

for i, mode in enumerate(modes):
    frame = ttk.LabelFrame(middle_frame, text=mode)
    frame.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
    middle_frame.columnconfigure(i, weight=1)
    mode_frames[mode] = frame

    fig, ax = plt.subplots(figsize=(4, 3))
    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    mode_canvases[mode] = (fig, ax, canvas)

# ========== Update Stats ==========
def update_stats():
    player = selected_player.get()
    opp = selected_opp.get()
    major = selected_major.get()
    ou = ou_line.get()

    data = df[df["player"] == player]
    if opp != "(All)":
        data = data[data["opponent"] == opp]
    if major != "(All)":
        data = data[data["major"] == major]

    # Filter to only maps 1–3 of each series
    maps13 = data[data["map"].isin([1, 2, 3])]

    if maps13.empty:
        avg_kills_var.set("No data")
        stdev_var.set("")
        med_kills_var.set("")
        conf_int_var.set("")
        total_kills_var.set("")
        map_count_var.set("")
        kd_var.set("")
        return

    kills = maps13["kills"]
    deaths = maps13["deaths"]

    avg_kills = kills.mean().round(2)
    stdev = kills.std().round(2)
    median = kills.median().round(2)
    conf_int = stats.t.interval(0.95, len(kills)-1, loc=avg_kills, scale=stats.sem(kills)) if len(kills) > 1 else (avg_kills, avg_kills)

    total_kills = kills.sum()
    total_deaths = deaths.sum()
    kd = (total_kills / total_deaths).round(2) if total_deaths != 0 else "∞"

    avg_kills_var.set(f"{avg_kills}")
    stdev_var.set(f"{stdev}")
    med_kills_var.set(f"{median}")
    conf_int_var.set(f"{round(conf_int[0],2)} to {round(conf_int[1],2)}")
    total_kills_var.set(f"{int(total_kills)}")
    map_count_var.set(f"{len(kills)}")
    kd_var.set(f"{kd}")

    # Update graphs
    for mode in modes:
        mode_data = maps13[maps13["mode"] == mode]
        kills = mode_data["kills"]

        fig, ax, canvas = mode_canvases[mode]
        ax.clear()
        if not kills.empty:
            ax.hist(kills, bins=10, color="#007acc", edgecolor="black")
            ax.axvline(ou, color="red", linestyle="--", label="O/U Line")
            ax.legend()
            ax.set_title(f"{mode} - Avg: {round(kills.mean(), 2)}")
            ax.set_xlabel("Kills")
            ax.set_ylabel("Maps")
        else:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center", fontsize=12)
        fig.tight_layout()
        canvas.draw()

# ========== Button ==========
ttk.Button(root, text="Generate Stats", command=update_stats).pack(pady=5)

# ========== Info ==========
info_frame = ttk.LabelFrame(root, text="How to Use")
info_frame.pack(fill='x', padx=10, pady=10)
info_text = ScrolledText(info_frame, height=4, wrap='word', font=("Segoe UI", 9))
info_text.pack(fill='x', padx=5, pady=5)
info_text.insert('end', "Select a player to view stats from the first 3 maps of each series. "
                        "Use the O/U Line to compare their performance. "
                        "Graphs show kills distribution for each mode with a red line for the O/U.")
info_text.configure(state='disabled')

# ========== Run ==========
update_stats()

root.mainloop()
