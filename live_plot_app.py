import streamlit as st
import numpy as np
import time

# Configuração da página do Streamlit
st.set_page_config(page_title="Gerador de Dados Live", layout="wide")

st.title("📶 Gerador e Plotagem Live de Temperatura")
st.markdown("Gera traços aleatórios de temperatura a cada 1 segundo. A cada 10 segundos um pico de temperatura é simulado.")

# Variáveis de estado para controlar a execução contínua
if 'trace_count' not in st.session_state:
    st.session_state.trace_count = 0
if 'running' not in st.session_state:
    st.session_state.running = False

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

update_interval = 0.2  # 200ms
traces_para_pico = int(10 / update_interval) if update_interval > 0 else 10
num_points = 1000
distances = np.linspace(0, 10000, num_points)

# st.fragment instrui o navegador a atualizar magicamente APENAS o conteúdo desta função
# a cada "update_interval" segundos, sem bloquear a página inteira ou os botões.
@st.fragment(run_every=update_interval)
def update_live_data():
    if st.session_state.running:
        st.session_state.trace_count += 1
        
        # Gera traço base aleatório
        base_temp = 25.0
        trace = base_temp + np.random.normal(0, 2.0, num_points)
        
        # Verifica se é a hora do pico
        is_peak = (st.session_state.trace_count % traces_para_pico == 0)
        
        if is_peak:
            peak_center = num_points // 2
            trace[peak_center-15:peak_center+15] += 50.0
            st.error(f"🔥 ALERTA! Pico de temperatura detectado! (Traço: {st.session_state.trace_count})")
        else:
            st.success(f"✅ Operação normal. (Traço: {st.session_state.trace_count})")
            
        # Desenha o gráfico na caixa do fragmento isolado
        st.line_chart(trace)
        
    else:
        st.warning("O gerador está parado. Clique em 'Iniciar'.")
        # Gráfico vazio para inicialização
        if st.session_state.trace_count == 0:
            st.line_chart([])

# Disparar renderização do fragmento parcial da tela
update_live_data()
