/**
 * Gerenciador de Simulações de Desconto
 * Sistema seguro que oculta a estrutura completa de bônus do usuário
 */

class SimulacaoManager {
    constructor() {
        this.config = null;
        this.distribuidoras = null;
        this.estados = null;
        this.tiposBonus = null;
        this.faixasConsumo = null;
        this.regrasDesconto = null;
        this.initialized = false;
    }

    async inicializar() {
        try {
            // Carregar todos os dados necessários
            const [config, distribuidoras, estados, tiposBonus, faixasConsumo, regrasDesconto] = await Promise.all([
                fetch('static/data/simulacao_config.json').then(r => r.json()),
                fetch('static/data/distribuidoras.json').then(r => r.json()),
                fetch('static/data/estados.json').then(r => r.json()),
                fetch('static/data/tipos_bonus.json').then(r => r.json()),
                fetch('static/data/faixas_consumo.json').then(r => r.json()),
                fetch('static/data/regras_desconto.json').then(r => r.json())
            ]);

            this.config = config;
            this.distribuidoras = distribuidoras;
            this.estados = estados;
            this.tiposBonus = tiposBonus;
            this.faixasConsumo = faixasConsumo;
            this.regrasDesconto = regrasDesconto;
            this.initialized = true;

            console.log('✅ Simulador inicializado com sucesso');
        } catch (error) {
            console.error('❌ Erro ao inicializar simulador:', error);
        }
    }

    /**
     * Verifica elegibilidade básica
     * @param {number} distribuidoraId - ID da distribuidora
     * @param {number} consumoKwh - Consumo em kWh
     * @returns {Object} Resultado da verificação
     */
    verificarElegibilidade(distribuidoraId, consumoKwh) {
        // Buscar distribuidora
        const distribuidora = this.distribuidoras.find(d => d.id === distribuidoraId);
        
        if (!distribuidora) {
            return {
                elegivel: false,
                erro: 'Distribuidora não encontrada'
            };
        }

        // Verificar se distribuidora está ativa
        if (!distribuidora.ativo) {
            return {
                elegivel: false,
                erro: 'Distribuidora não disponível no momento',
                distribuidora_nome: distribuidora.nome
            };
        }

        // Verificar consumo mínimo da distribuidora
        if (consumoKwh < distribuidora.consumo_minimo) {
            return {
                elegivel: false,
                erro: `Consumo mínimo para ${distribuidora.nome}: ${distribuidora.consumo_minimo} kWh`,
                consumo_minimo: distribuidora.consumo_minimo,
                distribuidora_nome: distribuidora.nome
            };
        }

        return {
            elegivel: true,
            distribuidora_nome: distribuidora.nome
        };
    }

    /**
     * Realiza simulação de desconto usando faixas de consumo e regras de desconto
     * @param {number} distribuidoraId - ID da distribuidora
     * @param {number} consumoKwh - Consumo em kWh
     * @returns {Object} Resultado da simulação
     */
    async simular(distribuidoraId, consumoKwh) {
        if (!this.initialized) {
            throw new Error('SimulacaoManager não foi inicializado');
        }

        try {
            // Validar entrada
            const validacao = this.validarConsumo(consumoKwh);
            if (!validacao.valido) {
                return {
                    elegivel: false,
                    motivo: validacao.erro,
                    consumo: consumoKwh
                };
            }

            // Verificar elegibilidade básica
            const elegibilidade = this.verificarElegibilidade(distribuidoraId, consumoKwh);
            if (!elegibilidade.elegivel) {
                return {
                    sucesso: false,
                    elegivel: false,
                    mensagem: elegibilidade.erro || this.config.mensagens.nao_apto,
                    consumo_minimo: elegibilidade.consumo_minimo,
                    distribuidora: elegibilidade.distribuidora_nome
                };
            }

            // Encontrar faixa de consumo da distribuidora
            const faixaConsumo = this.encontrarFaixaConsumo(distribuidoraId, consumoKwh);
            if (!faixaConsumo) {
                return {
                    elegivel: false,
                    motivo: 'Faixa de consumo não encontrada para esta distribuidora',
                    consumo: consumoKwh,
                    distribuidora: elegibilidade.distribuidora_nome
                };
            }

            // Buscar regra de desconto usando tipo de bonus padrão
            const tipoBonusPadraoId = this.config.configuracao.tipo_bonus_padrao_id;
            const regraDesconto = this.encontrarRegraDesconto(faixaConsumo.id, tipoBonusPadraoId);
            
            if (!regraDesconto) {
                return {
                    elegivel: false,
                    motivo: 'Regra de desconto não encontrada',
                    consumo: consumoKwh,
                    distribuidora: elegibilidade.distribuidora_nome
                };
            }

            // Buscar informações do tipo de bonus
            const tipoBonus = this.tiposBonus.find(tb => tb.id === tipoBonusPadraoId);

            return {
                sucesso: true,
                elegivel: true,
                consumo: consumoKwh,
                distribuidora: elegibilidade.distribuidora_nome,
                faixa_consumo: faixaConsumo,
                tipo_bonus: tipoBonus,
                desconto_percentual: regraDesconto.desconto_percentual,
                observacoes: regraDesconto.observacoes,
                mensagem: this.config.mensagens.apto,
                aviso_valores: this.config.mensagens.sem_calculo_valores
            };

        } catch (error) {
            console.error('Erro na simulação:', error);
            return {
                elegivel: false,
                motivo: this.config.mensagens.erro_calculo,
                erro: error.message
            };
        }
    }

    /**
     * Encontra a faixa de consumo adequada para uma distribuidora e consumo
     * @param {number} distribuidoraId - ID da distribuidora
     * @param {number} consumoKwh - Consumo em kWh
     * @returns {Object|null} Faixa de consumo encontrada
     */
    encontrarFaixaConsumo(distribuidoraId, consumoKwh) {
        if (!this.faixasConsumo) return null;
        
        return this.faixasConsumo.find(faixa => 
            faixa.distribuidora_id === distribuidoraId &&
            consumoKwh >= faixa.consumo_min &&
            (faixa.consumo_max === null || consumoKwh <= faixa.consumo_max)
        );
    }

    /**
     * Encontra a regra de desconto para uma faixa e tipo de bonus
     * @param {number} faixaConsumoId - ID da faixa de consumo
     * @param {number} tipoBonusId - ID do tipo de bonus
     * @returns {Object|null} Regra de desconto encontrada
     */
    encontrarRegraDesconto(faixaConsumoId, tipoBonusId) {
        if (!this.regrasDesconto) return null;
        
        return this.regrasDesconto.find(regra => 
            regra.faixa_consumo_id === faixaConsumoId &&
            regra.tipo_bonus_id === tipoBonusId
        );
    }

    /**
     * Obtém lista de distribuidoras por estado (apenas ativas)
     * @param {number} estadoId - ID do estado
     * @returns {Array} Lista de distribuidoras
     */
    obterDistribuidorasPorEstado(estadoId) {
        if (!this.distribuidoras) return [];
        
        // Converter para número para garantir comparação correta
        const estadoIdNum = parseInt(estadoId);
        
        return this.distribuidoras
            .filter(d => parseInt(d.estado_id) === estadoIdNum && d.ativo)
            .map(d => ({
                id: d.id,
                nome: d.nome,
                consumo_minimo: d.consumo_minimo,
                forma_pagamento: d.forma_pagamento,
                prazo_injecao: d.prazo_injecao
            }));
    }

    /**
     * Obtém lista de estados
     * @returns {Array} Lista de estados
     */
    obterEstados() {
        return this.estados || [];
    }

    /**
     * Obtém informações básicas de uma distribuidora
     * @param {number} distribuidoraId - ID da distribuidora
     * @returns {Object|null} Informações da distribuidora
     */
    obterInfoDistribuidora(distribuidoraId) {
        if (!this.distribuidoras) return null;
        
        const distribuidora = this.distribuidoras.find(d => d.id === distribuidoraId);
        if (!distribuidora) return null;

        return {
            id: distribuidora.id,
            nome: distribuidora.nome,
            consumo_minimo: distribuidora.consumo_minimo,
            forma_pagamento: distribuidora.forma_pagamento,
            prazo_injecao: distribuidora.prazo_injecao,
            aceita_placas: distribuidora.aceita_placas,
            observacoes: distribuidora.observacoes
        };
    }

    /**
     * Valida se o consumo está dentro dos limites
     * @param {number} consumoKwh - Consumo em kWh
     * @returns {Object} Resultado da validação
     */
    validarConsumo(consumoKwh) {
        const consumoNum = parseFloat(consumoKwh);
        
        if (isNaN(consumoNum) || consumoNum <= 0) {
            return {
                valido: false,
                erro: 'Consumo deve ser um número maior que zero'
            };
        }

        const min = this.config.regras_simulacao?.consumo_minimo_kwh || this.config.elegibilidade.consumo_minimo_global;
        const max = this.config.regras_simulacao?.consumo_maximo_kwh || 999999;
        
        if (consumoNum < min) {
            return {
                valido: false,
                erro: `Consumo mínimo deve ser ${min} kWh`
            };
        }
        
        if (consumoNum > max) {
            return {
                valido: false,
                erro: `Consumo máximo permitido é ${max} kWh`
            };
        }
        
        return {
            valido: true,
            consumo: Math.round(consumoNum)
        };
    }
}

// Instância global do simulador
const simulador = new SimulacaoManager();

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.SimulacaoManager = SimulacaoManager;
    window.simulador = simulador;
}

// Exportar para Node.js (se necessário)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SimulacaoManager, simulador };
}