# app.py
from flask import Flask, render_template, request
import math # Importamos math para arredondar

app = Flask(__name__)

# --- Rota 1: Calculadora de VO² máx (Rockport) ---
@app.route('/', methods=['GET', 'POST'])
def calculadora_vo2():
    resultado_vo2 = None
    if request.method == 'POST':
        peso_kg = float(request.form.get('peso'))
        idade = int(request.form.get('idade'))
        genero = int(request.form.get('genero'))
        tempo_min = int(request.form.get('tempo_minutos'))
        tempo_seg = int(request.form.get('tempo_segundos'))
        fc = int(request.form.get('frequencia_cardiaca'))
        
        peso_libras = peso_kg * 2.20462
        tempo_total_minutos = tempo_min + (tempo_seg / 60)
        
        vo2_calculado = 132.853 - (0.0769 * peso_libras) - (0.3877 * idade) + (6.315 * genero) - (3.2649 * tempo_total_minutos) - (0.1565 * fc)
        resultado_vo2 = f"{vo2_calculado:.2f}"

    return render_template('index.html', resultado_vo2=resultado_vo2)

# --- Rota 2: Calculadora de TMB e TMD  ---
@app.route('/tmb_tmd', methods=['GET', 'POST'])
def calculadora_tmb_tmd():
    resultado_tmb = None
    resultado_tmd = None
    
    if request.method == 'POST':
        peso = float(request.form.get('peso'))
        altura = float(request.form.get('altura'))
        idade = int(request.form.get('idade'))
        genero = request.form.get('genero')
        vo2max = float(request.form.get('vo2max'))

        # 1. Calcular TMB (Taxa Metabólica Basal)
        if genero == 'mulher':
            # Fórmula para Mulheres 
            tmb_calculada = 655 + (9.563 * peso) + (1.85 * altura) - (4.676 * idade)
        else: # 'homem'
            # Fórmula para Homens
            tmb_calculada = 66.5 + (13.75 * peso) + (5.003 * altura) - (6.755 * idade)
            
        # 2. Determinar F.A (Fator de Atividade) com base no VO² 
        fa = 1.3 # Valor base
        if genero == 'mulher':
            if vo2max >= 34.1:
                fa = 1.7
            elif vo2max >= 20.1:
                fa = 1.5
        else: # 'homem'
            if vo2max >= 36.1:
                fa = 1.7
            elif vo2max >= 20.1:
                fa = 1.5
                
        # 3. Calcular TMD (Taxa Metabólica Diária) 
        tmd_calculada = tmb_calculada * fa

        resultado_tmb = f"{tmb_calculada:.2f}"
        resultado_tmd = f"{tmd_calculada:.2f}"

    return render_template('tmb_tmd.html', resultado_tmb=resultado_tmb, resultado_tmd=resultado_tmd)

# --- Rota 3: Zona Alvo E Duração do Treino ---
@app.route('/planejamento_treino', methods=['GET', 'POST'])
def planejamento_treino():
    # Resultados para Zona Alvo
    resultado_zona_alvo = None
    # Resultados para Duração do Treino
    resultado_duracao = None
    passos_calculo = {} 
    
    erro = None
    form_data = {}

    if request.method == 'POST':
        try:
            # 1. Obter e converter TODAS as entradas
            idade = int(request.form.get('idade'))
            fc_repouso = int(request.form.get('fc_repouso'))
            peso = float(request.form.get('peso'))
            vo2max = float(request.form.get('vo2max'))
            intensidade_perc = int(request.form.get('intensidade_perc'))

            # Guarda os dados para re-preencher o formulário
            form_data = {
                'idade': idade, 'fc_repouso': fc_repouso, 'peso': peso, 
                'vo2max': vo2max, 'intensidade_perc': intensidade_perc
            }

            # =================================================================
            # PARTE 1: CÁLCULO DA ZONA ALVO (FC)
            # =================================================================
            
            # 1. FC Máxima (220 - Idade)
            fc_max = 220 - idade
            
            # 2. Desvio padrão
            desvio = 12 if idade > 25 else 10
            
            # 3. Limites da FC Máxima com desvio
            fc_max_inf = fc_max - desvio 
            fc_max_sup = fc_max + desvio 
            
            # 4. Reserva de FC (Inferior e Superior)
            reserva_inf = fc_max_inf - fc_repouso 
            reserva_sup = fc_max_sup - fc_repouso 
            
            # 5. Calcular Zona Alvo com base na intensidade 
            intensidade = intensidade_perc / 100.0
            
            limite_inf = (intensidade * reserva_inf) + fc_repouso 
            limite_sup = (intensidade * reserva_sup) + fc_repouso 
            
            resultado_zona_alvo = f"{math.ceil(limite_inf)} a {math.ceil(limite_sup)} bpm"

            # =================================================================
            # PARTE 2: CÁLCULO DA DURAÇÃO DO TREINO
            # =================================================================

            # Evita ZeroDivisionError
            if vo2max <= 3.5:
                 raise ZeroDivisionError 
                 
            # Passo 01: VO2 Reserva 
            vo2_res = vo2max - 3.5
            
            # Passo 02: VO2 Treino
            vo2_treino = (intensidade * vo2_res) + 3.5 # Usa a mesma intensidade da Parte 1
            
            # Passo 03: Converter VO2 Treino em MET
            met_treino = vo2_treino / 3.5
            
            # Passo 04: Kcal/min 
            kcal_min = (met_treino * 3.5 * peso) / 200
            
            # Passo 05: Gasto calórico recomendado (REC) 
            gasto_rec = (peso * 300) / 70
            
            # Passo 06: Duração do Treino 
            duracao_min = gasto_rec / kcal_min
            
            resultado_duracao = f"{math.ceil(duracao_min)} minutos"
            
            # Guardar passos intermédios
            passos_calculo = {
                'vo2_res': f"{vo2_res:.2f}",
                'vo2_treino': f"{vo2_treino:.2f}",
                'met_treino': f"{met_treino:.2f}",
                'kcal_min': f"{kcal_min:.2f}",
                'gasto_rec': f"{gasto_rec:.2f}"
            }
            
        except (ValueError, TypeError):
            erro = "Erro: Por favor, preencha todos os campos com números válidos."
        except ZeroDivisionError:
            erro = "Erro: O VO² Máx fornecido é muito baixo para este cálculo, resultando em divisão por zero."

    # Renderiza o template de planejamento com ambos os resultados
    return render_template('planejamento_treino.html', 
                           resultado_zona_alvo=resultado_zona_alvo, 
                           resultado_duracao=resultado_duracao, 
                           passos=passos_calculo, 
                           erro=erro, 
                           form_data=form_data)

if __name__ == '__main__':
    app.run(debug=True)