import matplotlib.pyplot as plt

class LabGUI:
    def __init__(self, titles):
        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'monospace'
        plt.rcParams['keymap.save'] = '' 
        
        self.fig = plt.figure(figsize=(15, 9), facecolor='#0b0b0b')
        grid = self.fig.add_gridspec(2, 4, hspace=0.35, wspace=0.4)
        
        self.ax_t = self.fig.add_subplot(grid[0, :2])
        self.ax_f = self.fig.add_subplot(grid[0, 2:])
        self.ax_i = self.fig.add_subplot(grid[1, 1:3])
        self.axs = [self.ax_t, self.ax_f, self.ax_i]
        self.titles = titles
        
        for ax in self.axs: ax.grid(True, color='#222222', linestyle=':')
        self.ax_i.set_aspect('equal', adjustable='box')
        
        self.sidebar = self.fig.text(0.76, 0.25, "", color='#00d4ff', fontsize=9, 
                                    bbox=dict(boxstyle='round', facecolor='#161616', alpha=0.8))
        plt.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.08)

    def update_focus(self, active_idx):
        for i, ax in enumerate(self.axs):
            color = '#00d4ff' if i == active_idx else 'white'
            ax.set_title(self.titles[i], color=color, weight='bold', fontsize=12 if i == active_idx else 10)