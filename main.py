import pandas as pd
import numpy as np
from scipy.stats import poisson
import streamlit as st

#Importando Dados
selecoes = pd.read_excel('dados//DadosCopaDoMundoQatar2022.xlsx', sheet_name='selecoes', index_col=0)
jogos = pd.read_excel('dados//DadosCopaDoMundoQatar2022.xlsx', sheet_name='jogos')
jogoscopa = pd.read_excel('dados//outputEstimativasJogosCopa.xlsx', index_col = 0)

# Transformação linear para uma escala de 0.15 até 1
fifa = selecoes['PontosRankingFIFA'] #Lista de seleções e score
vmin, vmax = min(fifa), max(fifa) #Obter valor min e max
fa, fb = 0.15, 1 #x-y
c_ang = (fb-fa)/(vmax-vmin) #Coef Angular - Intervalo minha escala / Intervalo Lista
c_lin = fb - c_ang*vmax #Coef Linear
forca = fifa*c_ang + c_lin

def media_gols(selecao1, selecao2):
    # Calcular média de gols
    # 2018 -> 2.64
    # 2022 -> 2.63
    forca1 = forca[selecao1]
    forca2 = forca[selecao2]
    media_gols = 2.63
    l1 = media_gols*forca1/(forca1 + forca2)
    l2 = media_gols - l1
    return [l1, l2]

def resultado(gols1, gols2):
    # Resultado em relação ao time 1
    if gols1 > gols2:
        return 'V'
    elif gols1 < gols2:
        return 'D'
    else:
        return 'E'

def pontos(gols1, gols2):
    #Pontuação Segundo FIFA
    result = resultado(gols1, gols2)
    if result == 'V':
        pontos1, pontos2 = 3, 0
    elif result == 'D':
        pontos1, pontos2 = 0, 3
    else:
        pontos1, pontos2 = 1, 1
    return [pontos1, pontos2, result]
        
def jogo(time1, time2):
    m1, m2 = media_gols(time1, time2) 
    gols1 = int(np.random.poisson(lam=m1, size=1)) #Simular gols em 1 partida com time de média de gols X
    gols2 = int(np.random.poisson(lam=m2, size=1))
    saldo1 = gols1 - gols2
    saldo2 = -saldo1
    pontos1, pontos2, result = pontos(gols1, gols2)
    placar = f'{gols1}x{gols2}'
    return [gols1, gols2, saldo1, saldo2, pontos1, pontos2, result, placar]

def distribuicao(media):
    # Calcular a probabilidade de X gols para uma média de Y
    probs = []
    # Probabilidade de fazer X gols até 7+
    for i in range(7):
        probs.append(poisson.pmf(i, media))
    # 7 gols ou mais
    # 1 - a soma de todas as probabilidades
    probs.append(1 - sum(probs))
    return probs

def percent_aux(var):
    # Retorna o valor em porcentagem
    return f'{str(round(100*var, 2))}%'


def probabilidade_partida(time1, time2):
    l1, l2 = media_gols(time1, time2) #Obter a média de gols do time
    d1, d2 = distribuicao(l1), distribuicao(l2) #Obter a prob de gols com base na média
    matriz = np.outer(d1, d2) #Calcular o produto de todos os valores
    vitoria = np.tril(matriz).sum()-np.trace(matriz) #Soma do triangulo sup - diagonal
    derrota = np.triu(matriz).sum()-np.trace(matriz) #Soma do triangulo inf - diagonal
    empate = 1-(vitoria+derrota) # diagonal
    probs = np.around([vitoria, empate, derrota], 3) #Arrendondar valores
    probsp = [f'{100*i:.1f}%' for i in probs]

    # Fomartação da matrix
    nomes_column = ['0', '1', '2', '3', '4', '5', '6', '7+']
    # Indexar colunas
    matriz = pd.DataFrame(matriz, columns=nomes_column, index=nomes_column)
    # MultiIndex com o nome do time
    matriz.index = pd.MultiIndex.from_product([[time1], matriz.index])
    matriz.columns = pd.MultiIndex.from_product([[time2], matriz.columns])
    #Arredondando valores
    forca1 = round(forca[time1], 2)
    forca2 = round(forca[time2], 2)
    media1 = round(l1, 2)
    media2 = round(l2, 2)
    # Montando JSON
    output = {
        'time1': time1,
        'time2': time2,
        'forca1': forca1,
        'forca2': forca2,
        'media1': media1,
        'media2': media2,
        'probabilidades':probsp,
        'matriz': matriz.applymap(percent_aux)
    }
    return output

### PAGINA USANDO STREAMLIT
st.set_page_config(
    page_title = 'Estatisticas - Jogos da Copa do Mundo',
    page_icon = '🏆',
)

st.markdown("# 🏆 Copa do Mundo - Qatar 2022")
st.markdown("## ⚽ Probabilidades das Partidas")
st.markdown('---')

lista_times1 = selecoes.index.tolist()
lista_times1.sort()
lista_times2 = lista_times1.copy()

column1, column2 = st.columns(2)
time1 = column1.selectbox('Escolha o primeiro time:', lista_times1)
lista_times2.remove(time1)
time2 = column2.selectbox('Escolha o segundo time:', lista_times2, index=1)

simulacao = probabilidade_partida(time1, time2)
prob = simulacao['probabilidades']
matriz = simulacao['matriz']

col1, col2, col3, col4, col5 = st.columns(5)
col1.image(selecoes.loc[time1, 'LinkBandeiraGrande'])
col2.metric(time1, prob[0])
col3.metric('Empate', prob[1])
col4.metric(time2, prob[2])
col5.image(selecoes.loc[time2, 'LinkBandeiraGrande'])

st.markdown('---')
st.markdown("## 📊 Probabilidades dos Placares")
st.table(matriz)

st.markdown('---')
st.markdown("## 🌍 Probabilidades dos Jogos da Copa")
st.table(jogoscopa[['grupo', 'seleção1', 'seleção2', 'Vitória', 'Empate', 'Derrota']])

st.markdown('---')
st.markdown('Desenvolvido :heart: por [Paulo Sampaio](https://github.com/paulovisam) :wave:')