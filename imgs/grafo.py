import matplotlib.pyplot as plt

requirements = [
    'Save File', 'New File', 'Open File', 'Close File', 'Print File',
    'Copy', 'Paste', 'Undo', 'Redo', 'Cut'
]

moscow_M = [12, 11, 11, 10, 8, 8, 8, 6, 6, 6]

# Frecuencias reales del CSS según tu mapeo al espacio reducido
css_freq = [10, 10, 10, 10, 3, 10, 10, 5, 2, 10]

fig, ax1 = plt.subplots(figsize=(12, 5))
ax2 = ax1.twinx()

ax1.bar(requirements, moscow_M, alpha=0.65, color='steelblue', label='MoSCoW (Must votes)')
ax2.plot(requirements, css_freq, color='darkred', marker='o', linewidth=2,
         label='CSS frequency')

ax1.set_ylabel('MoSCoW (Must votes)')
ax2.set_ylabel('Frequency in CSS')
ax1.set_xlabel('Original requirements')
plt.xticks(rotation=45, ha='right')
plt.title('Comparison between MoSCoW prioritization and structural importance')

handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper right')

plt.tight_layout()
plt.show()