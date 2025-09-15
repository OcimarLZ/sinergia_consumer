import re
import sys
import os
from bs4 import BeautifulSoup
from db_manager import DatabaseManager

class DataLoader:
    """Carregador de dados das distribuidoras a partir do HTML"""
    
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
            
            # Extrair estado e distribuidora do título
            # Formato esperado: "Quais são as condições para Estado (Distribuidora)?"
            match = re.search(r'para\s+([^(]+)\s*\(([^)]+)\)', titulo)
            if not match:
                return None
                
            estado_nome = match.group(1).strip()
            distribuidora_nome = match.group(2).strip()
            
            # Buscar conteúdo da resposta
            answer_div = details_element.find('div', class_='answer')
            if not answer_div:
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
                elif 'prazo de injeção' in texto_lower or 'injeção' in texto_lower:
                    dados['prazo_injecao'] = self.extrair_numero(texto)
                
                # Troca de titularidade
                elif 'troca de titularidade' in texto_lower:
                    dados['troca_titularidade'] = 'sim' in texto_lower
                
                # Desconto padrão
                elif 'desconto padrão' in texto_lower or 'desconto de' in texto_lower:
                    percentual = self.extrair_percentual(texto)
                    if percentual > 0:
                        # Determinar tipo de bônus
                        tipo_bonus = 'A'
                        if 'bônus b' in texto_lower:
                            tipo_bonus = 'B'
                        elif 'bônus c' in texto_lower:
                            tipo_bonus = 'C'
                        elif 'bônus d' in texto_lower:
                            tipo_bonus = 'D'
                        
                        dados['regras_desconto'].append({
                            'consumo_min': dados['consumo_minimo'],
                            'consumo_max': 999 if dados['consumo_minimo'] < 1000 else None,
                            'desconto_percentual': percentual,
                            'tipo_bonus': tipo_bonus,
                            'descricao': texto
                        })
                
                # Descontos opcionais
                elif 'descontos opcionais' in texto_lower or 'opcional' in texto_lower:
                    percentual = self.extrair_percentual(texto)
                    if percentual > 0:
                        tipo_bonus = 'B'
                        if 'bônus c' in texto_lower:
                            tipo_bonus = 'C'
                        elif 'bônus d' in texto_lower:
                            tipo_bonus = 'D'
                        
                        dados['regras_desconto'].append({
                            'consumo_min': dados['consumo_minimo'],
                            'consumo_max': 999,
                            'desconto_percentual': percentual,
                            'tipo_bonus': tipo_bonus,
                            'descricao': texto
                        })
                
                # Consumo acima de X kWh
                elif 'consumo acima de' in texto_lower or 'consumo de' in texto_lower:
                    consumo_min = self.extrair_numero(texto)
                    percentual = self.extrair_percentual(texto)
                    
                    if consumo_min > 0 and percentual > 0:
                        tipo_bonus = 'C'
                        if 'bônus d' in texto_lower:
                            tipo_bonus = 'D'
                        elif 'bônus b' in texto_lower:
                            tipo_bonus = 'B'
                        
                        # Determinar consumo máximo baseado no texto
                        consumo_max = None
                        if '1.000' in texto and '5.000' in texto:
                            consumo_max = 5000
                        elif '5.000' in texto and '10.000' in texto:
                            consumo_max = 10000
                        
                        dados['regras_desconto'].append({
                            'consumo_min': consumo_min,
                            'consumo_max': consumo_max,
                            'desconto_percentual': percentual,
                            'tipo_bonus': tipo_bonus,
                            'descricao': texto
                        })
                
                # Observações
                elif 'observações' in texto_lower:
                    observacoes_parts.append(texto)
                elif 'login e senha' in texto_lower:
                    dados['login_senha_necessario'] = 'necessário' in texto_lower
                    observacoes_parts.append(texto)
                elif 'icms' in texto_lower:
                    if 'não é permitido' in texto_lower:
                        dados['icms_minimo'] = 17.0
                    observacoes_parts.append(texto)
                elif 'placas' in texto_lower:
                    dados['aceita_placas'] = 'aceitamos' in texto_lower or 'podem aderir' in texto_lower
                    observacoes_parts.append(texto)
            
            # Buscar observações no parágrafo
            obs_p = answer_div.find('p')
            if obs_p and 'observações' in obs_p.get_text().lower():
                observacoes_parts.append(obs_p.get_text().strip())
            
            dados['observacoes'] = ' | '.join(observacoes_parts)
            
            return dados
            
        except Exception as e:
            print(f"Erro ao processar distribuidora: {e}")
            return None
    
    def carregar_dados_do_html(self, html_file_path: str):
        """Carrega dados das distribuidoras do arquivo HTML"""
        print("Iniciando carregamento de dados do HTML...")
        
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
        print(f"Encontradas {len(details_elements)} distribuidoras para processar...")
        
        distribuidoras_inseridas = 0
        
        for details in details_elements:
            dados = self.processar_distribuidora_html(details)
            if not dados:
                continue
            
            # Buscar ID do estado
            estado_id = estados_ids.get(dados['estado'])
            if not estado_id:
                print(f"Estado não encontrado: {dados['estado']}")
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
                print(f"✓ {dados['estado']} - {dados['distribuidora']} (ID: {distribuidora_id})")
                
            except Exception as e:
                print(f"✗ Erro ao inserir {dados['estado']} - {dados['distribuidora']}: {e}")
        
        print(f"\nCarregamento concluído! {distribuidoras_inseridas} distribuidoras inseridas.")
        
        # Mostrar estatísticas
        estados = self.db.listar_estados()
        print(f"Estados cadastrados: {len(estados)}")
        
        for estado in estados:
            distribuidoras = self.db.listar_distribuidoras_por_estado(estado['id'])
            if distribuidoras:
                print(f"  {estado['nome']} ({estado['sigla']}): {len(distribuidoras)} distribuidoras")

def main():
    """Função principal para executar o carregamento"""
    loader = DataLoader()
    
    # Caminho para o arquivo HTML
    html_path = os.path.join(os.path.dirname(__file__), '..', 'index.html')
    
    if not os.path.exists(html_path):
        print(f"Arquivo HTML não encontrado: {html_path}")
        return
    
    loader.carregar_dados_do_html(html_path)

if __name__ == "__main__":
    main()