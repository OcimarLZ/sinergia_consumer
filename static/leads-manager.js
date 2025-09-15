// Gerenciador de Leads
class LeadsManager {
  constructor() {
    this.storageKey = 'sinergia_leads';
  }

  // Salvar lead no localStorage
  salvarLead(leadData, simulacaoData) {
    const lead = {
      id: this.gerarId(),
      timestamp: new Date().toISOString(),
      dados_pessoais: {
        nome: leadData.nome,
        email: leadData.email,
        whatsapp: leadData.whatsapp
      },
      simulacao: {
        estado: simulacaoData.estado,
        distribuidora: simulacaoData.distribuidora,
        consumo_kwh: simulacaoData.consumo,
        valor_conta: simulacaoData.valorConta,
        desconto_percentual: simulacaoData.desconto,
        economia_mensal: simulacaoData.economiaMensal,
        economia_anual: simulacaoData.economiaAnual,
        elegivel: simulacaoData.elegivel,
        motivo: simulacaoData.motivo || null
      },
      status: 'novo',
      origem: 'landing_page'
    };

    // Recuperar leads existentes
    const leads = this.obterLeads();
    leads.push(lead);

    // Salvar no localStorage
    localStorage.setItem(this.storageKey, JSON.stringify(leads));

    // Também salvar em arquivo JSON (simulação para desenvolvimento)
    this.salvarEmArquivo(leads);

    return lead;
  }

  // Obter todos os leads
  obterLeads() {
    try {
      const leads = localStorage.getItem(this.storageKey);
      return leads ? JSON.parse(leads) : [];
    } catch (error) {
      console.error('Erro ao recuperar leads:', error);
      return [];
    }
  }

  // Gerar ID único
  gerarId() {
    return 'lead_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Simular salvamento em arquivo (para desenvolvimento)
  salvarEmArquivo(leads) {
    // Em produção, isso seria enviado para um servidor
    // Por enquanto, apenas logamos no console
    console.log('Leads salvos:', leads);
    
    // Criar blob para download (opcional para testes)
    const blob = new Blob([JSON.stringify(leads, null, 2)], {
      type: 'application/json'
    });
    
    // Salvar referência para possível download
    window.leadsData = leads;
  }

  // Exportar leads para download
  exportarLeads() {
    const leads = this.obterLeads();
    const blob = new Blob([JSON.stringify(leads, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads_sinergia_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Limpar todos os leads (para desenvolvimento)
  limparLeads() {
    localStorage.removeItem(this.storageKey);
    console.log('Leads limpos');
  }

  // Obter estatísticas dos leads
  obterEstatisticas() {
    const leads = this.obterLeads();
    return {
      total: leads.length,
      elegiveis: leads.filter(l => l.simulacao.elegivel).length,
      nao_elegiveis: leads.filter(l => !l.simulacao.elegivel).length,
      economia_total_mensal: leads
        .filter(l => l.simulacao.elegivel)
        .reduce((sum, l) => sum + (l.simulacao.economia_mensal || 0), 0)
    };
  }
}

// Instância global
window.leadsManager = new LeadsManager();