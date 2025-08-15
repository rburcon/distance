import streamlit as st
import pandas as pd
import numpy as np
import pvlib
from pvlib.tools import cosd, sind
from datetime import datetime, time
import matplotlib.pyplot as plt

# Configuração da página DEVE SER A PRIMEIRA OPERAÇÃO DO STREAMLIT
st.set_page_config(page_title="Calculadora de Espaçamento entre Fileiras", page_icon="☀️", layout="wide")

# Carregar dados das cidades
@st.cache_data
def load_cities():
    df = pd.read_csv('location.csv')
    df['CIDADE_UF'] = df['MUNICIPIO'] + '-' + df['UF']
    return df

# Restante do código...
cities_df = load_cities()

# Configuração da sidebar recolhível
with st.sidebar:
    st.title("☀️ Configurações")
    
    with st.expander("📏 Dimensões dos Painéis", expanded=True):
        num_paineis_vertical = st.number_input("Número de painéis na vertical", min_value=1, value=2)
        altura_painel = st.number_input("Altura do painel (m)", min_value=0.1, value=2.2, step=0.1)
        largura_painel = st.number_input("Largura do painel (m)", min_value=0.1, value=1.0, step=0.1)
    
    with st.expander("📐 Orientação do Sistema", expanded=False):
        tilt = st.number_input("Ângulo de inclinação (graus)", min_value=0, max_value=90, value=20)
        azimuth = st.number_input("Azimute (graus, 0=Sul, -90=Leste, +90=Oeste)", 
                                 min_value=-180, max_value=180, value=0)
    
    with st.expander("🌍 Localização", expanded=False):
        # Selecionar cidade
        default_city = "MARINGA-PR"
        city_options = sorted(cities_df['CIDADE_UF'].unique())
        default_index = city_options.index(default_city) if default_city in city_options else 0
        city_uf = st.selectbox("Selecione a Cidade-UF:", city_options, index=default_index)
        
        # Obter coordenadas da cidade selecionada
        city_data = cities_df[cities_df['CIDADE_UF'] == city_uf].iloc[0]
        latitude = float(city_data['LATITUDE'].replace(',', '.'))
        longitude = float(city_data['LONGITUDE'].replace(',', '.'))
        
        st.write(f"Coordenadas: {latitude:.4f}° N, {longitude:.4f}° W")
        
        altitude = st.number_input("Altitude (m)", min_value=0, value=800)
    
    with st.expander("⏱ Parâmetros de Tempo", expanded=False):
        data_calculo = st.date_input("Data para cálculo (solstício de inverno)", 
                                    value=pd.to_datetime("2023-06-21"))
    
    st.markdown("---")
    calcular_btn = st.button("Calcular Distância entre Fileiras", type="primary")
    st.markdown("---")
    
    # Seção de informações
    st.info("""
    **Instruções:**
    1. Preencha todos os parâmetros
    2. Clique no botão calcular
    3. Visualize os resultados na página principal
    """)

# Conteúdo principal
st.title("Calculadora de Distância entre Fileiras de Painéis Solares")

st.markdown("""
Esta ferramenta calcula a distância mínima necessária entre fileiras de painéis solares para evitar sombreamento 
entre 9:30 e 14:00 (horário solar local), considerando o pior caso (solstício de inverno).
""")

# Função para cálculo da distância entre fileiras
def calcular_distancia_fileiras(latitude, tilt, altura_total, azimuth, date, longitude, altitude):
    # Criar localização
    location = pvlib.location.Location(latitude, longitude, tz='UTC', altitude=altitude)
    
    # Definir faixa de horário para análise (9:30 às 14:30)
    times = pd.date_range(
        start=pd.Timestamp(date).replace(hour=9, minute=30),
        end=pd.Timestamp(date).replace(hour=14, minute=30),
        freq='5min',
        tz=location.tz
    )
    
    # Obter posição do sol
    solpos = location.get_solarposition(times)
    
    # Calcular o pior caso (maior sombra)
    # Encontrar o ângulo solar mais baixo no período
    idx_min_altitude = solpos.apparent_zenith.idxmin()
    solar_zenith = solpos.loc[idx_min_altitude, 'apparent_zenith']
    solar_azimuth = solpos.loc[idx_min_altitude, 'azimuth']
    
    # Calcular comprimento da sombra
    altura_sistema = altura_total * sind(tilt)
    comprimento_sombra = altura_sistema / np.tan(np.radians(solar_zenith))
    
    # Calcular distância entre fileiras considerando azimute
    delta_azimuth = solar_azimuth - azimuth
    distancia_fileiras = comprimento_sombra * abs(cosd(delta_azimuth)) + largura_painel * cosd(tilt)
    
    return distancia_fileiras, solar_zenith, solar_azimuth, idx_min_altitude

# Calcular quando o botão for pressionado
if calcular_btn:
    altura_total = num_paineis_vertical * altura_painel
    
    try:
        with st.spinner('Calculando...'):
            distancia, zenit, azimute_solar, hora_pior_caso = calcular_distancia_fileiras(
                latitude, tilt, altura_total, azimuth, data_calculo, longitude, altitude
            )
        
        # Mostrar resultados em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            st.success(f"**Distância mínima entre fileiras:** {distancia:.2f} metros")
            
            # Mostrar detalhes do cálculo
            st.subheader("📊 Detalhes do Cálculo")
            st.write(f"- **Cidade selecionada:** {city_uf}")
            st.write(f"- **Data de cálculo:** {data_calculo.strftime('%d/%m/%Y')}")
            st.write(f"- **Hora do pior caso:** {hora_pior_caso.strftime('%H:%M')}")
            st.write(f"- **Ângulo zenital solar:** {zenit:.1f}°")
            st.write(f"- **Azimute solar:** {azimute_solar:.1f}°")
            st.write(f"- **Altura total do sistema:** {altura_total:.2f} m")
            st.write(f"- **Altura vertical do sistema:** {(altura_total * sind(tilt)):.2f} m")
        
        
        
    except Exception as e:
        st.error(f"Ocorreu um erro no cálculo: {str(e)}")
else:
    st.info("💡 Configure os parâmetros na barra lateral e clique em 'Calcular' para obter os resultados.")

# Rodapé
st.markdown("---")
st.caption("Desenvolvido usando Python, Streamlit e PVLib | © 2023")