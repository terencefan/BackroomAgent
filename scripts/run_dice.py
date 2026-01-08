import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.utils.dice import Dice

def run_simulation(sides, trials=100000):
    dice = Dice()
    
    print(f"  - Rolling Normal x {trials}")
    results_normal = [dice.roll(sides) for _ in range(trials)]
    
    print(f"  - Rolling Advantage x {trials}")
    results_adv = [dice.roll(sides, advantage=True) for _ in range(trials)]
    
    print(f"  - Rolling Disadvantage x {trials}")
    results_dis = [dice.roll(sides, disadvantage=True) for _ in range(trials)]
    
    return results_normal, results_adv, results_dis

def plot_distribution(sides, results, filename):
    normal, adv, dis = results
    
    # Create 3 subplots horizontally, sharing Y axis for fair comparison
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    fig.suptitle(f'd{sides} Probability Distribution (N={len(normal)})', fontsize=16)

    # Bins setup
    bins = np.arange(1, sides + 2) - 0.5
    
    datasets = [
        (dis, 'Disadvantage', 'red'),
        (normal, 'Normal', 'gray'),
        (adv, 'Advantage', 'green')
    ]

    for ax, (data, label, color) in zip(axes, datasets):
        ax.hist(data, bins=bins, density=True, color=color, edgecolor='black', alpha=0.7)
        ax.set_title(label, color=color, fontsize=14, fontweight='bold')
        ax.set_xlabel('Roll Result')
        ax.set_xlim(0.5, sides + 0.5)
        ax.grid(True, alpha=0.2, linestyle='--')
        
        # Mean line
        mean_val = np.mean(data)
        ax.axvline(mean_val, color='black', linestyle='dashed', linewidth=2)
        
        # Mean text (placed near the top or near the line)
        # Using transformation to place text relative to axes
        ax.text(mean_val, ax.get_ylim()[1] * 0.95 if ax.get_ylim()[1] > 0 else 0.05, 
                f' Avg: {mean_val:.1f}', color='black', rotation=90, 
                verticalalignment='top', horizontalalignment='right', fontweight='bold')

    axes[0].set_ylabel('Probability')
    
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Saved plot to {filename}")
    plt.close()

if __name__ == "__main__":
    # Ensure tmp directory exists
    os.makedirs("tmp", exist_ok=True)

    print("Simulating d20...")
    d20_res = run_simulation(20)
    plot_distribution(20, d20_res, "tmp/d20_distribution.png")
    
    print("\nSimulating d100...")
    # Reduce trials slightly for d100 just in case, but 100k is fast enough usually
    d100_res = run_simulation(100)
    plot_distribution(100, d100_res, "tmp/d100_distribution.png")
