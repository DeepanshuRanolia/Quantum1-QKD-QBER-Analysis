
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================
# 1. LOAD DATA
# =====================================================

df = pd.read_csv("qber_experiment_results.csv")

# Ensure Boolean values are correctly interpreted
df["key_agreement"] = (
    df["key_agreement"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({"true": True, "false": False})
)

if df["key_agreement"].isna().any():
    raise ValueError("Invalid values found in key_agreement column.")

methods = ["Hamming", "BCH", "LDPC"]

# Convert QBER to percentage for plotting
df["channel_qber_percent"] = df["channel_qber"] * 100
df["estimated_qber_percent"] = df["estimated_qber"] * 100

# =====================================================
# 2. CALCULATE STATISTICS
# =====================================================

summary = (
    df.groupby(["channel_qber", "method"])
    .agg(
        success_rate=("key_agreement", "mean"),

        mean_efficiency=("efficiency", "mean"),
        std_efficiency=("efficiency", "std"),

        mean_runtime=("execution_time", "mean"),
        std_runtime=("execution_time", "std"),

        mean_failed_blocks=("failed_blocks", "mean"),
        std_failed_blocks=("failed_blocks", "std"),

        mean_disclosed_bits=("disclosed_bits", "mean"),
        mean_processed_bits=("processed_bits", "mean"),
        mean_remaining_bits=("remaining_bits", "mean"),

        mean_initial_errors=("initial_errors", "mean")
    )
    .reset_index()
)

summary["channel_qber_percent"] = summary["channel_qber"] * 100

summary.to_csv("qber_summary.csv", index=False)

qber_values = sorted(df["channel_qber"].unique())
qber_percent = [q * 100 for q in qber_values]

print("\nEXPERIMENTAL SUMMARY")
print(summary.to_string(index=False))

print("\nSUCCESSFUL TRIALS")
print(
    df.groupby(["channel_qber_percent", "method"])
    ["key_agreement"].sum()
)

# =====================================================
# 3. COMMON PLOT SETTINGS
# =====================================================

def prepare_plot(title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.set_title(
        title,
        fontsize=14,
        fontweight="bold",
        pad=15
    )

    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)

    ax.set_xticks(qber_percent)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)

    return fig, ax


# =====================================================
# PLOT 1: QBER VS KEY AGREEMENT SUCCESS RATE
# =====================================================

fig, ax = prepare_plot(
    "Key Agreement Success Rate vs Channel QBER",
    "Channel QBER (%)",
    "Success Rate (%)"
)

x = np.arange(len(qber_values))
width = 0.25

for i, method in enumerate(methods):

    data = summary[summary["method"] == method]

    values = [
        data.loc[
            data["channel_qber"] == q,
            "success_rate"
        ].iloc[0] * 100
        for q in qber_values
    ]

    bars = ax.bar(
        x + (i - 1) * width,
        values,
        width,
        label=method,
        edgecolor="black",
        linewidth=0.6
    )

    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:.1f}%",
            xy=(bar.get_x() + bar.get_width()/2, value),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=8
        )

ax.set_xticks(x)
ax.set_xticklabels([f"{q:g}%" for q in qber_percent])
ax.set_ylim(0, 115)
ax.legend(title="Method")

plt.tight_layout()
plt.savefig("plot1_success_rate.png", dpi=300)
plt.show()


# =====================================================
# PLOT 2: QBER VS RECONCILIATION EFFICIENCY
# =====================================================

fig, ax = prepare_plot(
    "Reconciliation Efficiency vs Channel QBER",
    "Channel QBER (%)",
    "Reconciliation Efficiency"
)

for method in methods:

    data = summary[summary["method"] == method]

    ax.errorbar(
        data["channel_qber_percent"],
        data["mean_efficiency"],
        yerr=data["std_efficiency"],
        marker="o",
        capsize=4,
        linewidth=2,
        markersize=6,
        label=method
    )

ax.legend(title="Method")

plt.tight_layout()
plt.savefig("plot2_efficiency.png", dpi=300)
plt.show()


# =====================================================
# PLOT 3: QBER VS EXECUTION TIME
# =====================================================

fig, ax = prepare_plot(
    "Execution Time vs Channel QBER",
    "Channel QBER (%)",
    "Execution Time (seconds)"
)

for method in methods:

    data = summary[summary["method"] == method]

    ax.errorbar(
        data["channel_qber_percent"],
        data["mean_runtime"],
        yerr=data["std_runtime"],
        marker="o",
        capsize=4,
        linewidth=2,
        markersize=6,
        label=method
    )

ax.legend(title="Method")

plt.tight_layout()
plt.savefig("plot3_execution_time.png", dpi=300)
plt.show()


# =====================================================
# PLOT 4: QBER VS FAILED BLOCKS
# =====================================================

fig, ax = prepare_plot(
    "Failed Blocks vs Channel QBER",
    "Channel QBER (%)",
    "Mean Number of Failed Blocks"
)

for method in methods:

    data = summary[summary["method"] == method]

    ax.errorbar(
        data["channel_qber_percent"],
        data["mean_failed_blocks"],
        yerr=data["std_failed_blocks"],
        marker="o",
        capsize=4,
        linewidth=2,
        markersize=6,
        label=method
    )

ax.legend(title="Method")

plt.tight_layout()
plt.savefig("plot4_failed_blocks.png", dpi=300)
plt.show()


# =====================================================
# PLOT 5: QBER VS DISCLOSED BITS
# =====================================================

fig, ax = prepare_plot(
    "Disclosed Bits vs Channel QBER",
    "Channel QBER (%)",
    "Mean Number of Disclosed Bits"
)

for method in methods:

    data = summary[summary["method"] == method]

    ax.plot(
        data["channel_qber_percent"],
        data["mean_disclosed_bits"],
        marker="o",
        linewidth=2,
        markersize=6,
        label=method
    )

ax.legend(title="Method")

plt.tight_layout()
plt.savefig("plot5_disclosed_bits.png", dpi=300)
plt.show()


# =====================================================
# PLOT 6: PROCESSED VS REMAINING BITS
# =====================================================

fig, axes = plt.subplots(
    1, 2,
    figsize=(13, 5)
)

for ax, method in zip(axes, methods):

    data = summary[summary["method"] == method]

    ax.plot(
        data["channel_qber_percent"],
        data["mean_processed_bits"],
        marker="o",
        linewidth=2,
        label="Processed bits"
    )

    ax.plot(
        data["channel_qber_percent"],
        data["mean_remaining_bits"],
        marker="s",
        linewidth=2,
        label="Remaining bits"
    )

    ax.set_title(method, fontweight="bold")
    ax.set_xlabel("Channel QBER (%)")
    ax.set_ylabel("Mean Number of Bits")
    ax.set_xticks(qber_percent)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()

fig.suptitle(
    "Processed and Remaining Bits vs Channel QBER",
    fontsize=14,
    fontweight="bold"
)

plt.tight_layout()
plt.savefig("plot6_processed_remaining_bits.png", dpi=300)
plt.show()


# =====================================================
# PLOT 7: CHANNEL QBER VS ESTIMATED QBER
# =====================================================

qber_estimate = (
    df.groupby("channel_qber")
    .agg(
        mean_estimated_qber=("estimated_qber", "mean"),
        std_estimated_qber=("estimated_qber", "std")
    )
    .reset_index()
)

fig, ax = plt.subplots(figsize=(8, 5.5))

ax.errorbar(
    qber_estimate["channel_qber"] * 100,
    qber_estimate["mean_estimated_qber"] * 100,
    yerr=qber_estimate["std_estimated_qber"] * 100,
    marker="o",
    capsize=4,
    linewidth=2,
    label="Estimated QBER"
)

ax.plot(
    qber_percent,
    qber_percent,
    linestyle="--",
    label="Ideal estimation"
)

ax.set_title(
    "Estimated QBER vs Actual Channel QBER",
    fontsize=14,
    fontweight="bold"
)

ax.set_xlabel("Channel QBER (%)")
ax.set_ylabel("Estimated QBER (%)")
ax.set_xticks(qber_percent)
ax.grid(True, linestyle="--", alpha=0.35)
ax.legend()

plt.tight_layout()
plt.savefig("plot7_qber_estimation.png", dpi=300)
plt.show()


# =====================================================
# PLOT 8: QBER VS INITIAL ERRORS
# =====================================================

initial_error_summary = (
    df.groupby("channel_qber")
    .agg(
        mean_errors=("initial_errors", "mean"),
        std_errors=("initial_errors", "std")
    )
    .reset_index()
)

fig, ax = plt.subplots(figsize=(8, 5.5))

ax.errorbar(
    initial_error_summary["channel_qber"] * 100,
    initial_error_summary["mean_errors"],
    yerr=initial_error_summary["std_errors"],
    marker="o",
    capsize=4,
    linewidth=2,
    markersize=6
)

ax.set_title(
    "Initial Bit Errors vs Channel QBER",
    fontsize=14,
    fontweight="bold"
)

ax.set_xlabel("Channel QBER (%)")
ax.set_ylabel("Mean Number of Initial Errors")
ax.set_xticks(qber_percent)
ax.grid(True, linestyle="--", alpha=0.35)

plt.tight_layout()
plt.savefig("plot8_initial_errors.png", dpi=300)
plt.show()


# =====================================================
# 9. FINAL MESSAGE
# =====================================================

print("\nALL ANALYSIS COMPLETED SUCCESSFULLY!")

print("\nGenerated plots:")
print("1. plot1_success_rate.png")
print("2. plot2_efficiency.png")
print("3. plot3_execution_time.png")
print("4. plot4_failed_blocks.png")
print("5. plot5_disclosed_bits.png")
print("6. plot6_processed_remaining_bits.png")
print("7. plot7_qber_estimation.png")
print("8. plot8_initial_errors.png")

print("\nSummary saved as qber_summary.csv")

import pandas as pd
import matplotlib.pyplot as plt

# Load block-level diagnostics
df = pd.read_csv("block_error_results.csv")

# Calculate success percentage for each error weight
summary = (
    df.groupby(["method", "error_weight"])
      .agg(
          total_blocks=("success", "count"),
          successful_blocks=("success", "sum")
      )
      .reset_index()
)

summary["success_rate"] = (
    summary["successful_blocks"] / summary["total_blocks"] * 100
)

print("\n========== ERROR-CORRECTION CAPABILITY ==========")
print(summary.to_string(index=False))

# Plot
plt.figure(figsize=(10, 6))

for method in summary["method"].unique():
    method_data = summary[summary["method"] == method]

    plt.plot(
        method_data["error_weight"],
        method_data["success_rate"],
        marker="o",
        linewidth=2,
        label=method
    )

plt.xlabel("Number of Errors in a Block")
plt.ylabel("Successful Correction Rate (%)")
plt.title("Error-Correction Capability: Hamming vs BCH vs LDPC")

plt.xticks(sorted(df["error_weight"].unique()))
plt.ylim(-5, 105)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig("error_correction_capability.png", dpi=300)
plt.show()
