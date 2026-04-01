import streamlit as st
import numpy as np
import time
import plotly.graph_objects as go

# Configuração da página do Streamlit
st.set_page_config(page_title="Gerador de Dados Live", layout="wide")

st.title("📶 Gerador e Plotagem Live de Temperatura")
st.markdown("Gera traços aleatórios de temperatura a cada 1 segundo. A cada 10 segundos um pico de temperatura é simulado.")

# Variáveis de estado para controlar a execução contínua
if 'trace_count' not in st.session_state:
    st.session_state.trace_count = 0
if 'running' not in st.session_state:
    st.session_state.running = False
if 'history' not in st.session_state:
    st.session_state.history = []

# Botões de controle
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Iniciar / Continuar", use_container_width=True):
        st.session_state.running = True
        st.rerun()
with col2:
    if st.button("⏸️ Parar", use_container_width=True):
        st.session_state.running = False
        st.rerun()

update_interval = 0.1  # 1s
traces_para_pico = int(10 / update_interval) if update_interval > 0 else 10
num_points = 1000
distances = np.linspace(0, 1000, num_points)

# st.fragment instrui o navegador a atualizar magicamente APENAS o conteúdo desta função
# a cada "update_interval" segundos, sem bloquear a página inteira ou os botões.
@st.fragment(run_every=update_interval)
def update_live_data():
    if st.session_state.running:
        st.session_state.trace_count += 1
        
        # Gera traço base com ciclo solar simulado e random walk (ruído coerente)
        # O ciclo completo ocorre a cada 1440 traços (simulando 1 dia inteiro)
        ciclo_solar = 15.0 * np.sin(2 * np.pi * st.session_state.trace_count / 1440.0)
        
        # Noise coerente (random walk restrito)
        if 'ambient_noise' not in st.session_state:
            st.session_state.ambient_noise = 0.0
        st.session_state.ambient_noise += np.random.normal(0, 0.5)
        st.session_state.ambient_noise = np.clip(st.session_state.ambient_noise, -5.0, 5.0)
        
        base_temp = 25.0 + ciclo_solar + st.session_state.ambient_noise
        trace = base_temp + np.random.normal(0, 2.0, num_points)
        
        # Verifica se é a hora do pico
        is_peak = (st.session_state.trace_count % traces_para_pico == 0)
        
        if is_peak:
            # Hotspot em local aleatório ao longo do cabo/distância
            peak_center = np.random.randint(15, num_points - 15)
            trace[peak_center-15:peak_center+15] += 50.0
            st.error(f"🔥 ALERTA! Pico detectado em {distances[peak_center]:.1f}m! (Traço: {st.session_state.trace_count})")
        else:
            st.success(f"✅ Operação normal. (Traço: {st.session_state.trace_count})")
            
        # Adiciona ao histórico do gráfico 2D (limite de 1440 traços para simular o dia inteiro)
        st.session_state.history.append(trace)
        if len(st.session_state.history) > 1440:
            st.session_state.history.pop(0)
            
        st.markdown("### Gráfico 1D - Temperatura Atual")
        # Desenha o gráfico 1D
        st.line_chart(trace)
        
        st.markdown("### Gráfico 2D - Histórico Acumulativo de Temperatura")
        if len(st.session_state.history) > 0:
            z_data = np.array(st.session_state.history)
            fig = go.Figure(data=go.Heatmap(
                z=z_data,
                x=distances,
                colorscale='jet',
                zmin=15,
                zmax=80
            ))
            # Configurando os ticks do eixo Y para mostrar de 0h a 24h
            tickvals = np.arange(0, 1441, 60)
            ticktext = [f"{int(h/60)}h" for h in tickvals]
            
            fig.update_layout(
                xaxis_title="Distância (m)",
                yaxis_title="Hora do Dia",
                yaxis=dict(
                    tickmode='array',
                    tickvals=tickvals,
                    ticktext=ticktext
                ),
                margin=dict(l=0, r=0, t=30, b=0),
                height=650
            )
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.warning("O gerador está parado. Clique em 'Iniciar'.")
        # Gráfico vazio para inicialização
        if st.session_state.trace_count == 0:
            st.line_chart([])

# Disparar renderização do fragmento parcial da tela
update_live_data()
