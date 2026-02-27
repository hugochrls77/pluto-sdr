import matplotlib.pyplot as plt

class LabGUI:
    def __init__(self, titles):
        self.fig = plt.figure(figsize=(12, 8), facecolor='#0b0e14')
        self.axs = [self.fig.add_subplot(2, 2, i) for i in [1, 2, 4]]
        self.ax_t, self.ax_f, self.ax_i = self.axs
        
        for ax, title in zip(self.axs, titles):
            ax.set_facecolor('#11151c')
            ax.set_title(title, color='#00d4ff', fontsize=10, fontweight='bold')
            ax.tick_params(colors='white', labelsize=8)
            ax.grid(True, alpha=0.1)

        self.sidebar = self.fig.text(0.70, 0.25, "", color='white', 
                                    fontsize=9, family='monospace',
                                    bbox=dict(facecolor='#1a1f26', alpha=0.8, edgecolor='#00d4ff'))
        plt.tight_layout(rect=[0, 0, 0.65, 1])

    def update_focus(self, active_plot):
        for i, ax in enumerate(self.axs):
            for spine in ax.spines.values():
                spine.set_color('#00d4ff' if i == active_plot else '#333b4d')
                spine.set_linewidth(2 if i == active_plot else 1)

    def handle_interaction(self, event, active_plot, zx, zy):
        """Gère les zooms et le focus de manière universelle."""
        if event.key in ['1', '2', '3']:
            active_plot = int(event.key) - 1
        elif event.key == 't':
            active_plot = (active_plot + 1) % 3
        elif event.key == 'up':
            zy[active_plot] *= 0.5  # Zoom vertical plus sec pour les signaux faibles
        elif event.key == 'down':
            zy[active_plot] *= 2.0  # Dé-zoom pour voir les signaux saturés
        elif event.key == '+':
            zx[active_plot] *= 1.5
        elif event.key == '-':
            zx[active_plot] = max(1.0, zx[active_plot] / 1.5)
            
        return active_plot, zx, zy