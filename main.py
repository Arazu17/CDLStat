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

# Main window setup
root = tk.Tk()
root.title("CDL Player Prop Statlab")
root.geometry("1100x800")

# ========== Top Filters Area ==========
top_frame = ttk.Frame(root)
top_frame.pack(fill='x', padx=10, pady=5)

# Dropdowns
players = df["player"].unique().tolist()
opponents = ["(All)"] + sorted(df["opponent"].dropna().unique().tolist())
majors = ["(All)"] + sorted(df["major"].dropna().unique().tolist())

selected_player = tk.StringVar(value=players[0])
selected_opp = tk.StringVar(value="(All)")
selected_major = tk.StringVar(value="(All)")
ou_line = tk.DoubleVar(value=51.5)
selected_player.trace_add("write", lambda *args: update_stats())
selected_opp.trace_add("write", lambda *args: update_stats())
selected_major.trace_add("write", lambda *args: update_stats())


ttk.Label(top_frame, text="Player:").pack(side="left")
ttk.Combobox(top_frame, textvariable=selected_player, values=players, state="readonly", width=15).pack(side="left", padx=5)

ttk.Label(top_frame, text="Maps 1-3 O/U Line:").pack(side="left")
ttk.Entry(top_frame, textvariable=ou_line, width=10).pack(side="left", padx=5)

ttk.Label(top_frame, text="Opponent:").pack(side="left")
ttk.Combobox(top_frame, textvariable=selected_opp, values=opponents, state="readonly", width=15).pack(side="left", padx=5)

ttk.Label(top_frame, text="Major:").pack(side="left")
ttk.Combobox(top_frame, textvariable=selected_major, values=majors, state="readonly", width=15).pack(side="left", padx=5)

# ========== Stats Display Area ==========
stats_frame = ttk.Frame(root)
stats_frame.pack(fill='x', padx=10, pady=5)

avg_kills_var = tk.StringVar()
stdev_var = tk.StringVar()
med_kills_var = tk.StringVar()
conf_int_var = tk.StringVar()

ttk.Label(stats_frame, textvariable=avg_kills_var, width=25).pack(side="left", padx=5)
ttk.Label(stats_frame, textvariable=stdev_var, width=25).pack(side="left", padx=5)
ttk.Label(stats_frame, textvariable=med_kills_var, width=25).pack(side="left", padx=5)
ttk.Label(stats_frame, textvariable=conf_int_var, width=35).pack(side="left", padx=5)

# ========== Mode Panels ==========
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

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    mode_canvases[mode] = (fig, ax, canvas)

# ========== Stats Function ==========
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

    if data.empty:
        avg_kills_var.set("No data")
        stdev_var.set("")
        med_kills_var.set("")
        conf_int_var.set("")
        return

    total_kills = data["kills"]
    avg_kills = total_kills.mean().round(2)
    stdev = total_kills.std().round(2)
    median = total_kills.median().round(2)
    conf_int = stats.t.interval(0.95, len(total_kills)-1, loc=avg_kills, scale=stats.sem(total_kills)) if len(total_kills) > 1 else (avg_kills, avg_kills)

    avg_kills_var.set(f"Maps 1-3 Avg. Kills: {avg_kills}")
    stdev_var.set(f"St. Dev: {stdev}")
    med_kills_var.set(f"Median: {median}")
    conf_int_var.set(f"95% CI: {round(conf_int[0],2)}, {round(conf_int[1],2)}")

    # Update histograms for each mode
    for mode in modes:
        mode_data = data[data["mode"] == mode]
        kills = mode_data["kills"]

        fig, ax, canvas = mode_canvases[mode]
        ax.clear()
        if not kills.empty:
            ax.hist(kills, bins=10, color="#4da6ff", edgecolor="black")
            ax.set_title(f"{mode} - Avg: {round(kills.mean(), 2)}")
            ax.set_xlabel("Kills")
            ax.set_ylabel("Maps")
        else:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center", fontsize=12)
        canvas.draw()

# ========== Button ==========
ttk.Button(root, text="Generate Stats", command=update_stats).pack(pady=5)

# Initial Stats
update_stats()

root.mainloop()
