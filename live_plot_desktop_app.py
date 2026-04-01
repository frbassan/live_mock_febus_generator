import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ==========================================
# Configurações Iniciais
# ==========================================
update_interval_ms = 100  # Intervalo de atualização super rápido para testar performance
traces_para_pico = int(10 / (update_interval_ms / 1000.0))
num_points = 1000
distances = np.linspace(0, 1000, num_points)

# Variáveis de Estado - TEMPERATURA
trace_count = 0
max_history = 1440
history_array_temp = np.full((max_history, num_points), 55.0)  # Pré-aloca a matriz
ambient_noise_temp = 0.0
active_peaks_temp = []

# Variáveis de Estado - STRAIN
history_array_strain = np.full((max_history, num_points), 0.0)
ambient_noise_strain = 0.0
active_peaks_strain = []

# Variáveis de Estado - ALERTAS
alerts_temp = []
alerts_strain = []
max_alerts_display = 12

# ==========================================
# Configuração da Janela (Matplotlib Native)
# ==========================================
from matplotlib.gridspec import GridSpec

plt.style.use('dark_background')

fig = plt.figure(figsize=(30, 8))
fig.canvas.manager.set_window_title("DTSS plot")
# Para jogar totalmente para a esquerda, além de ha='left', precisamos ancorar o xismo (x) no começo da tela (ex: 5% = 0.05)
fig.suptitle("DTSS plot", fontsize=16, x=0.05, ha='left')

# Usando GridSpec para reservar espaço específico para Cbar e Painéis de Alertas ao lado do 1D
gs = GridSpec(2, 6, width_ratios=[1, 0.02, 0.15, 1, 0.02, 0.15], height_ratios=[1, 2.5])

ax1_temp = fig.add_subplot(gs[0, 0])
ax2_temp = fig.add_subplot(gs[1, 0], sharex=ax1_temp)
cax_temp = fig.add_subplot(gs[1, 1])

ax1_strain = fig.add_subplot(gs[0, 3])
ax2_strain = fig.add_subplot(gs[1, 3], sharex=ax1_strain)
cax_strain = fig.add_subplot(gs[1, 4])

# Configuração visual da 'Caixa de Texto' (com fundo escuro e borda)
bbox_props = dict(boxstyle="round,pad=0.4", fc="#1c1c1c", ec="#555555", lw=1)

# Painéis de Alertas Individuais (Coluna direita de cada respectivo gráfico)
ax_alerts_temp = fig.add_subplot(gs[0, 1])
ax_alerts_temp.axis('off')
ax_alerts_temp.set_title("Temperature Warnings", color='white', loc='left', fontsize=10)
# POSIÇÃO: (0.0, 1.0) define X (0% à esquerda) e Y (100% no topo) do painel
text_alerts_temp = ax_alerts_temp.text(0.0, 1.0, "", color='yellow', fontsize=9, 
                                       verticalalignment='top', transform=ax_alerts_temp.transAxes, 
                                       family='monospace', bbox=bbox_props)

ax_alerts_strain = fig.add_subplot(gs[0, 4])
ax_alerts_strain.axis('off')
ax_alerts_strain.set_title("Strain Warnings", color='white', loc='left', fontsize=10)
# POSIÇÃO: (0.0, 1.0) define X (0% à esquerda) e Y (100% no topo) do painel
text_alerts_strain = ax_alerts_strain.text(0.0, 1.0, "", color='yellow', fontsize=9, 
                                           verticalalignment='top', transform=ax_alerts_strain.transAxes, 
                                           family='monospace', bbox=bbox_props)

# --- Gráfico 1D TEMPERATURA ---
line_temp, = ax1_temp.plot(distances, np.zeros(num_points), color='#ff4500', lw=1.2)
ax1_temp.set_xlim(0, 1000)
ax1_temp.set_ylim(0, 250)
ax1_temp.set_ylabel("Temperature (°C)")
ax1_temp.grid(True, linestyle='--', alpha=0.3)
ax1_temp.set_title("Temperature")

# --- Gráfico 1D STRAIN ---
line_strain, = ax1_strain.plot(distances, np.zeros(num_points), color='#00ffcc', lw=1.2)
ax1_strain.set_xlim(0, 1000)
ax1_strain.set_ylim(-1000, 1000)
ax1_strain.set_ylabel("Strain (μE)")
ax1_strain.grid(True, linestyle='--', alpha=0.3)
ax1_strain.set_title("Strain")

# --- Gráfico 2D TEMPERATURA ---
im_temp = ax2_temp.imshow(
    history_array_temp, aspect='auto', origin='lower', cmap='jet', vmin=0, vmax=200, extent=[0, 1000, 0, 24]
)
ax2_temp.set_xlabel("Length (m)")
ax2_temp.set_ylabel("Hour")
ax2_temp.set_yticks(np.arange(0, 25, 2))
ax2_temp.set_yticklabels([f"{h}h" for h in range(0, 25, 2)])
cbar_temp = fig.colorbar(im_temp, cax=cax_temp, orientation='vertical')
cbar_temp.set_label("Temperature (°C)")

# --- Gráfico 2D STRAIN ---
im_strain = ax2_strain.imshow(
    history_array_strain, aspect='auto', origin='lower', cmap='viridis', vmin=-1000, vmax=1000, extent=[0, 1000, 0, 24]
)
ax2_strain.set_xlabel("Length (m)")
ax2_strain.set_ylabel("Hour")
ax2_strain.set_yticks(np.arange(0, 25, 2))
ax2_strain.set_yticklabels([f"{h}h" for h in range(0, 25, 2)])
cbar_strain = fig.colorbar(im_strain, cax=cax_strain, orientation='vertical')
cbar_strain.set_label("Strain (μE)")

plt.tight_layout()

# --- Linha Divisória Central ---
# Traça uma linha vertical decorativa dividindo a tela ao meio (0.5 do eixo X da Figura)
div_line = plt.Line2D([0.48, 0.48], [0.05, 0.95], transform=fig.transFigure, color='gray', linestyle='--', linewidth=1, alpha=0.5)
fig.add_artist(div_line)

# ==========================================
# Loop de Atualização
# ==========================================
def update(frame):
    global trace_count 
    global ambient_noise_temp, history_array_temp, active_peaks_temp
    global ambient_noise_strain, history_array_strain, active_peaks_strain
    global alerts_temp, alerts_strain
    
    trace_count += 1
    
    # -----------------------------------------------------
    # LÓGICA DE TEMPERATURA
    # -----------------------------------------------------
    # 1. Ciclo solar: Base = 55. Amplitude = 45 -> Vai de 10 a 100°C
    ciclo_solar_temp = 45.0 * np.sin(2 * np.pi * trace_count / 1440.0)
    
    # Ruído ambiente Temp
    ambient_noise_temp += np.random.normal(0, 0.5)
    ambient_noise_temp = np.clip(ambient_noise_temp, -10.0, 10.0)
    
    base_temp = 55.0 + ciclo_solar_temp + ambient_noise_temp
    trace_temp = base_temp + np.random.normal(0, 2.0, num_points)
    
    # Picos de Temperatura
    if trace_count % traces_para_pico == 0:
        peak_center = np.random.randint(15, num_points - 15)
        max_abs_temp = np.random.uniform(0.0, 200.0)
        delta_temp = max_abs_temp - trace_temp[peak_center]
        active_peaks_temp.append({
            'center': peak_center,
            'temp': 0.0,
            'max_temp': delta_temp,
            'phase': 'rising'
        })
        evento_tipo = "🔥 CALOR" if delta_temp > 0 else "❄️ FRIO"
        prefix = "T+" if delta_temp > 0 else "T-"
        print(f"{evento_tipo}! Foco iniciado em {distances[peak_center]:.1f}m! (Traço: {trace_count})")
        new_alert = {
            'pos_m': distances[peak_center],
            'target': max_abs_temp,
            'base': trace_temp[peak_center],
            'current': trace_temp[peak_center],
            'prefix': prefix
        }
        alerts_temp.insert(0, new_alert)
        alerts_temp = alerts_temp[:max_alerts_display]
        active_peaks_temp[-1]['alert_ref'] = new_alert
        
    for p in active_peaks_temp[:]:
        step = 4.0 if p['max_temp'] > 0 else -4.0
        fall_step = 2.0 if p['max_temp'] > 0 else -2.0
        
        if p['phase'] == 'rising':
            p['temp'] += step
            if 'alert_ref' in p:
                p['alert_ref']['current'] = p['alert_ref']['base'] + p['temp']
                
            if abs(p['temp']) >= abs(p['max_temp']):
                p['phase'] = 'falling'
                if 'alert_ref' in p:
                    p['alert_ref']['current'] = p['alert_ref']['target'] # Congela o texto no valor máximo atingido
        else:
            p['temp'] -= fall_step
            if (step > 0 and p['temp'] <= 0) or (step < 0 and p['temp'] >= 0):
                active_peaks_temp.remove(p)
                continue
        c = p['center']
        trace_temp[c-5:c+5] += p['temp']
        
    # Limita fisicamente a renderização ao teto e piso
    trace_temp = np.clip(trace_temp, a_min=0.0, a_max=200.0)
        
    # -----------------------------------------------------
    # LÓGICA DE STRAIN
    # -----------------------------------------------------
    # Ruído ambiente Strain (ex: vento/vibração lenta tensionando o cabo)
    ambient_noise_strain += np.random.normal(0, 5.0)
    ambient_noise_strain = np.clip(ambient_noise_strain, -200.0, 200.0)
    
    trace_strain = ambient_noise_strain + np.random.normal(0, 15.0, num_points)
    
    # Picos Mecânicos
    # Frequência um pouco diferente dos Picos de calor
    if trace_count % int(traces_para_pico * 1.5) == 0:
        peak_center = np.random.randint(10, num_points - 10)
        # Valores contínuos entre 50 e 800, tracionando ou comprimindo
        max_strain = np.random.uniform(50.0, 800.0) * np.random.choice([1, -1])
        active_peaks_strain.append({
            'center': peak_center,
            'strain': 0.0,
            'max_strain': max_strain, # Eventos de alongamento ou compressão
            'phase': 'rising'
        })
        evento_tipo = "📈 TRAÇÃO" if max_strain > 0 else "📉 COMPRESSÃO"
        prefix = "S+" if max_strain > 0 else "S-"
        print(f"{evento_tipo}! Evento mecânico iniciado em {distances[peak_center]:.1f}m! (Traço: {trace_count})")
        new_alert = {
            'pos_m': distances[peak_center],
            'target': max_strain,
            'current': 0.0,
            'prefix': prefix
        }
        alerts_strain.insert(0, new_alert)
        alerts_strain = alerts_strain[:max_alerts_display]
        active_peaks_strain[-1]['alert_ref'] = new_alert
        
    for p in active_peaks_strain[:]:
        step = 20.0 if p['max_strain'] > 0 else -20.0
        
        if p['phase'] == 'rising':
            p['strain'] += step
            if 'alert_ref' in p:
                p['alert_ref']['current'] = p['strain']
                
            if abs(p['strain']) >= abs(p['max_strain']):
                p['phase'] = 'falling'
                if 'alert_ref' in p:
                    p['alert_ref']['current'] = p['alert_ref']['target'] # Congela no valor máximo
        else:
            p['strain'] -= step
            if (step > 0 and p['strain'] <= 0) or (step < 0 and p['strain'] >= 0):
                active_peaks_strain.remove(p)
                continue
        c = p['center']
        trace_strain[c-10:c+10] += p['strain']
    
    # -----------------------------------------------------
    # ATUALIZAÇÃO VISUAL
    # -----------------------------------------------------
    # 1D
    line_temp.set_ydata(trace_temp)
    line_strain.set_ydata(trace_strain)
    
    # 2D Hitóricos
    if trace_count <= max_history:
        history_array_temp[trace_count-1] = trace_temp
        history_array_strain[trace_count-1] = trace_strain
    else:
        history_array_temp = np.roll(history_array_temp, shift=-1, axis=0)
        history_array_temp[-1] = trace_temp
        
        history_array_strain = np.roll(history_array_strain, shift=-1, axis=0)
        history_array_strain[-1] = trace_strain
        
    im_temp.set_data(history_array_temp)
    im_strain.set_data(history_array_strain)
    
    current_traces = min(trace_count, max_history)
    im_temp.set_extent([0, 1000, 0, current_traces / 60.0])
    im_strain.set_extent([0, 1000, 0, current_traces / 60.0])
    
    # Prepara o texto formatado das listas de dicionários
    str_alerts_temp = [f"{a['prefix']} {a['pos_m']:.0f}m ({a['current']:.0f}°C)" for a in alerts_temp]
    str_alerts_strain = [f"{a['prefix']} {a['pos_m']:.0f}m ({a['current']:+.0f}μE)" for a in alerts_strain]
    
    text_alerts_temp.set_text("\n".join(str_alerts_temp))
    text_alerts_strain.set_text("\n".join(str_alerts_strain))
    
    return line_temp, line_strain, im_temp, im_strain, text_alerts_temp, text_alerts_strain

# interval=update_interval_ms indica quanto tempo esperar entre os frames
ani = animation.FuncAnimation(fig, update, interval=update_interval_ms, blit=False, cache_frame_data=False)
plt.show()
