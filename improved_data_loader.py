import re
import sys
import os
from bs4 import BeautifulSoup
from database.db_manager import DatabaseManager

class ImprovedDataLoader:
    """Carregador melhorado de dados das distribuidoras a partir do HTML"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.estados_map = {
            'Alagoas': 'AL',
            'Bahia': 'BA', 
            'Ceará': 'CE',
            'Espírito Santo': 'ES',
            'Goiás': 'GO',
            'Maranhão': 'MA',
            'Mato Grosso': 'MT',
            'Mato Grosso do Sul': 'MS',
            'Minas Gerais': 'MG',
            'Pará': 'PA',
            'Paraíba': 'PB',
            'Paraná': 'PR',
            'Pernambuco': 'PE',
            'Piauí': 'PI',
            'Rio de Janeiro': 'RJ',
            'Rio Grande do Norte': 'RN',
            'Rio Grande do Sul': 'RS',
            'Santa Catarina': 'SC',
            'São Paulo': 'SP',
            'Tocantins': 'TO'
        }
    
    def extrair_numero(self, texto: str) -> int:
        """Extrai número de um texto"""
        match = re.search(r'(\d+)', texto.replace('.', '').replace(',', ''))
        return int(match.group(1)) if match else 0
    
    def extrair_percentual(self, texto: str) -> float:
        """Extrai percentual de um texto"""
        match = re.search(r'(\d+(?:\.\d+)?)%', texto)
        return float(match.group(1)) if match else 0.0
    
    def processar_distribuidora_html(self, details_element):
        """Processa um elemento <details> de distribuidora do HTML"""
        try:
            # Extrair título (estado e distribuidora)
            summary = details_element.find('summary')
            if not summary:
                return None
                
            titulo = summary.get_text().strip()
            print(f"Processando: {titulo}")
            
            # Extrair estado e distribuidora do título
            # Formato esperado: "Quais são as condições para Estado (Distribuidora)?"
            match = re.search(r'para\s+([^(]+)\s*\(([^)]+)\)', titulo)
            if not match:
                print(f"  ❌ Não foi possível extrair estado/distribuidora do título")
                return None
                
            estado_nome = match.group(1).strip()
            distribuidora_nome = match.group(2).strip()
            
            # Normalizar nomes de estados
            if estado_nome == 'o Rio Grande do Sul':
                estado_nome = 'Rio Grande do Sul'
            elif estado_nome == 'o Rio de Janeiro':
                estado_nome = 'Rio de Janeiro'
            elif estado_nome == 'o Rio Grande do Norte':
                estado_nome = 'Rio Grande do Norte'
            elif estado_nome == 'o Ceará':
                estado_nome = 'Ceará'
            elif estado_nome == 'o Piauí':
                estado_nome = 'Piauí'
            elif estado_nome == 'o Pará':
                estado_nome = 'Pará'
            elif estado_nome == 'a Bahia':
                estado_nome = 'Bahia'
            elif estado_nome == 'o Espírito Santo':
                estado_nome = 'Espírito Santo'
            elif estado_nome == 'o Mato Grosso':
                estado_nome = 'Mato Grosso'
            elif estado_nome == 'o Mato Grosso do Sul':
                estado_nome = 'Mato Grosso do Sul'
            
            print(f"  Estado: {estado_nome}, Distribuidora: {distribuidora_nome}")
            
            # Buscar conteúdo da resposta
            answer_div = details_element.find('div', class_='answer')
            if not answer_div:
                print(f"  ❌ Div de resposta não encontrada")
                return None
            
            # Extrair dados da lista
            lista_items = answer_div.find_all('li')
            
            dados = {
                'estado': estado_nome,
                'distribuidora': distribuidora_nome,
                'consumo_minimo': 100,  # padrão
                'forma_pagamento': 'Unificado',  # padrão
                'prazo_injecao': 90,  # padrão
                'troca_titularidade': False,
                'login_senha_necessario': False,
                'aceita_placas': True,
                'icms_minimo': 17.0,
                'observacoes': '',
                'regras_desconto': []
            }
            
            observacoes_parts = []
            
            for item in lista_items:
                texto = item.get_text().strip()
                texto_lower = texto.lower()
                
                # Consumo mínimo
                if 'consumo' in texto_lower and ('mínimo' in texto_lower or 'de' in texto_lower):
                    dados['consumo_minimo'] = self.extrair_numero(texto)
                
                # Forma de pagamento
                elif 'forma de pagamento' in texto_lower or 'pagamento' in texto_lower:
                    if 'dois boletos' in texto_lower:
                        dados['forma_pagamento'] = 'Dois Boletos'
                    elif 'unificado' in texto_lower:
                        dados['forma_pagamento'] = 'Unificado'
                
                # Prazo de injeção
                elif 'prazo' in texto_lower and 'injeção' in texto_lower:
                    dados['prazo_injecao'] = self.extrair_numero(texto)
                
                # Troca de titularidade
                elif 'troca de titularidade' in texto_lower:
                    dados['troca_titularidade'] = 'sim' in texto_lower
                
                # Login e senha
                elif 'login' in texto_lower and 'senha' in texto_lower:
                    dados['login_senha_necessario'] = 'necessário' in texto_lower or 'obrigatório' in texto_lower
                
                # Placas
                elif 'placas' in texto_lower:
                    if 'não permitido' in texto_lower or 'não aceita' in texto_lower:
                        dados['aceita_placas'] = False
                    elif 'aceita' in texto_lower or 'permitido' in texto_lower:
                        dados['aceita_placas'] = True
                
                # ICMS
                elif 'icms' in texto_lower:
                    icms_num = self.extrair_numero(texto)
                    if icms_num > 0:
                        dados['icms_minimo'] = float(icms_num)
                
                # Descontos
                elif any(palavra in texto_lower for palavra in ['desconto', 'bônus', '%']):
                    percentual = self.extrair_percentual(texto)
                    if percentual > 0:
                        # Determinar faixa de consumo
                        consumo_min = 0
                        consumo_max = None
                        
                        if 'acima de 1.000' in texto_lower or 'acima de 1000' in texto_lower:
                            consumo_min = 1000
                        elif 'acima de 5.000' in texto_lower or 'acima de 5000' in texto_lower:
                            consumo_min = 5000
                        elif 'acima de 10.000' in texto_lower or 'acima de 10000' in texto_lower:
                            consumo_min = 10000
                        
                        # Determinar tipo de bônus
                        tipo_bonus = 'Padrão'
                        if 'bônus a' in texto_lower:
                            tipo_bonus = 'Bônus A'
                        elif 'bônus b' in texto_lower:
                            tipo_bonus = 'Bônus B'
                        elif 'bônus c' in texto_lower:
                            tipo_bonus = 'Bônus C'
                        elif 'bônus d' in texto_lower:
                            tipo_bonus = 'Bônus D'
                        
                        dados['regras_desconto'].append({
                            'consumo_min': consumo_min,
                            'consumo_max': consumo_max,
                            'desconto_percentual': percentual,
                            'tipo_bonus': tipo_bonus,
                            'descricao': texto
                        })
            
            # Extrair observações
            observacoes_element = answer_div.find('p')
            if observacoes_element and 'observações' in observacoes_element.get_text().lower():
                dados['observacoes'] = observacoes_element.get_text().strip()
            
            print(f"  ✅ Dados extraídos com sucesso")
            return dados
            
        except Exception as e:
            print(f"  ❌ Erro ao processar distribuidora: {e}")
            return None
    
    def carregar_dados_do_html(self, html_file_path: str):
        """Carrega dados das distribuidoras do arquivo HTML"""
        print("Iniciando carregamento melhorado de dados do HTML...")
        
        # Limpar dados existentes
        self.db.limpar_dados()
        
        # Ler arquivo HTML
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Inserir estados
        print("Inserindo estados...")
        estados_ids = {}
        for estado_nome, sigla in self.estados_map.items():
            estado_id = self.db.inserir_estado(estado_nome, sigla)
            estados_ids[estado_nome] = estado_id
        
        # Encontrar seção de distribuidoras
        distribuidoras_section = soup.find('section', id='distribuidoras')
        if not distribuidoras_section:
            print("Seção de distribuidoras não encontrada!")
            return
        
        # Processar cada distribuidora
        details_elements = distribuidoras_section.find_all('details', class_='faq-item')
        print(f"Encontradas {len(details_elements)} distribuidoras para processar...\n")
        
        distribuidoras_inseridas = 0
        
        for details in details_elements:
            dados = self.processar_distribuidora_html(details)
            if not dados:
                continue
            
            # Buscar ID do estado
            estado_id = estados_ids.get(dados['estado'])
            if not estado_id:
                print(f"❌ Estado não encontrado: {dados['estado']}")
                continue
            
            try:
                # Inserir distribuidora
                distribuidora_id = self.db.inserir_distribuidora(
                    nome=dados['distribuidora'],
                    estado_id=estado_id,
                    consumo_minimo=dados['consumo_minimo'],
                    forma_pagamento=dados['forma_pagamento'],
                    prazo_injecao=dados['prazo_injecao'],
                    troca_titularidade=dados['troca_titularidade'],
                    login_senha_necessario=dados['login_senha_necessario'],
                    aceita_placas=dados['aceita_placas'],
                    icms_minimo=dados['icms_minimo'],
                    observacoes=dados['observacoes']
                )
                
                # Inserir regras de desconto
                for regra in dados['regras_desconto']:
                    self.db.inserir_regra_desconto(
                        distribuidora_id=distribuidora_id,
                        consumo_min=regra['consumo_min'],
                        consumo_max=regra['consumo_max'],
                        desconto_percentual=regra['desconto_percentual'],
                        tipo_bonus=regra['tipo_bonus'],
                        descricao=regra['descricao']
                    )
                
                distribuidoras_inseridas += 1
                print(f"✅ {dados['estado']} - {dados['distribuidora']} (ID: {distribuidora_id})\n")
                
            except Exception as e:
                print(f"❌ Erro ao inserir {dados['estado']} - {dados['distribuidora']}: {e}\n")
        
        print(f"\nCarregamento concluído! {distribuidoras_inseridas} distribuidoras inseridas.")
        
        # Mostrar estatísticas
        estados = self.db.listar_estados()
        print(f"Estados cadastrados: {len(estados)}")
        
        for estado in estados:
            distribuidoras = self.db.listar_distribuidoras_por_estado(estado['id'])
            if distribuidoras:
                print(f"  {estado['nome']} ({estado['sigla']}): {len(distribuidoras)} distribuidoras")

def main():
    loader = ImprovedDataLoader()
    
    # Caminho do arquivo HTML
    html_file = 'index.html'
    
    if not os.path.exists(html_file):
        print(f"Arquivo {html_file} não encontrado!")
        return
    
    loader.carregar_dados_do_html(html_file)
    print("\nProcesso concluído!")

if __name__ == "__main__":
    main()