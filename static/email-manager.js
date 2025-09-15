// Gerenciador de E-mails com EmailJS
class EmailManager {
  constructor() {
    // Configurações do EmailJS (você precisa configurar sua conta)
    this.serviceId = 'YOUR_SERVICE_ID'; // Substitua pelo seu Service ID
    this.templateId = 'YOUR_TEMPLATE_ID'; // Substitua pelo seu Template ID
    this.publicKey = 'YOUR_PUBLIC_KEY'; // Substitua pela sua Public Key
    
    // Inicializar EmailJS
    this.inicializar();
  }

  // Inicializar EmailJS
  inicializar() {
    // Verificar se EmailJS está carregado
    if (typeof emailjs !== 'undefined') {
      emailjs.init(this.publicKey);
      console.log('EmailJS inicializado');
    } else {
      console.warn('EmailJS não carregado. Verifique se o script está incluído.');
    }
  }

  // Enviar e-mail com dados da simulação
  async enviarSimulacao(leadData, simulacaoData) {
    try {
      // Verificar se EmailJS está disponível
      if (typeof emailjs === 'undefined') {
        throw new Error('EmailJS não está carregado');
      }

      // Preparar dados para o template
      const templateParams = {
        to_email: leadData.email,
        to_name: leadData.nome,
        from_name: 'Sinergia Energia',
        
        // Dados pessoais
        cliente_nome: leadData.nome,
        cliente_email: leadData.email,
        cliente_whatsapp: leadData.whatsapp,
        
        // Dados da simulação
        estado: simulacaoData.estado,
        distribuidora: simulacaoData.distribuidora,
        consumo_kwh: simulacaoData.consumo,
        valor_conta: this.formatarMoeda(simulacaoData.valorConta),
        desconto_percentual: simulacaoData.desconto,
        economia_mensal: this.formatarMoeda(simulacaoData.economiaMensal),
        economia_anual: this.formatarMoeda(simulacaoData.economiaAnual),
        elegivel: simulacaoData.elegivel ? 'Sim' : 'Não',
        motivo: simulacaoData.motivo || 'N/A',
        
        // Data da simulação
        data_simulacao: new Date().toLocaleDateString('pt-BR'),
        hora_simulacao: new Date().toLocaleTimeString('pt-BR'),
        
        // Mensagem personalizada
        mensagem_resultado: this.gerarMensagemResultado(simulacaoData)
      };

      // Enviar e-mail
      const response = await emailjs.send(
        this.serviceId,
        this.templateId,
        templateParams
      );

      console.log('E-mail enviado com sucesso:', response);
      return { sucesso: true, response };

    } catch (error) {
      console.error('Erro ao enviar e-mail:', error);
      return { sucesso: false, erro: error.message };
    }
  }

  // Gerar mensagem personalizada baseada no resultado
  gerarMensagemResultado(simulacaoData) {
    if (simulacaoData.elegivel) {
      return `Ótimas notícias! Você pode economizar R$ ${this.formatarMoeda(simulacaoData.economiaMensal)} por mês (${simulacaoData.desconto}% de desconto) com a portabilidade de energia. Entre em contato conosco para dar continuidade ao processo.`;
    } else {
      return `Infelizmente, com base no seu perfil atual, você não atende aos critérios para portabilidade de energia. Motivo: ${simulacaoData.motivo}. Entre em contato conosco para mais informações sobre outras opções disponíveis.`;
    }
  }

  // Formatar valor em moeda brasileira
  formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  }

  // Enviar e-mail de notificação para a equipe comercial
  async notificarEquipeComercial(leadData, simulacaoData) {
    try {
      const templateParams = {
        to_email: 'comercial@sinergia.com.br', // E-mail da equipe comercial
        to_name: 'Equipe Comercial',
        from_name: 'Sistema de Leads',
        
        subject: `Novo Lead: ${leadData.nome} - ${simulacaoData.elegivel ? 'ELEGÍVEL' : 'NÃO ELEGÍVEL'}`,
        
        // Dados do lead
        lead_nome: leadData.nome,
        lead_email: leadData.email,
        lead_whatsapp: leadData.whatsapp,
        lead_status: simulacaoData.elegivel ? 'ELEGÍVEL' : 'NÃO ELEGÍVEL',
        
        // Dados da simulação
        simulacao_estado: simulacaoData.estado,
        simulacao_distribuidora: simulacaoData.distribuidora,
        simulacao_consumo: simulacaoData.consumo,
        simulacao_economia: this.formatarMoeda(simulacaoData.economiaMensal || 0),
        simulacao_desconto: simulacaoData.desconto || 0,
        
        // Timestamp
        data_lead: new Date().toLocaleString('pt-BR')
      };

      // Usar template específico para equipe comercial
      const response = await emailjs.send(
        this.serviceId,
        'template_equipe_comercial', // Template específico para equipe
        templateParams
      );

      console.log('Notificação enviada para equipe comercial:', response);
      return { sucesso: true, response };

    } catch (error) {
      console.error('Erro ao notificar equipe comercial:', error);
      return { sucesso: false, erro: error.message };
    }
  }

  // Configurar credenciais do EmailJS
  configurar(serviceId, templateId, publicKey) {
    this.serviceId = serviceId;
    this.templateId = templateId;
    this.publicKey = publicKey;
    this.inicializar();
  }

  // Testar configuração do EmailJS
  async testarConfiguracao() {
    try {
      const testParams = {
        to_email: 'teste@exemplo.com',
        to_name: 'Teste',
        from_name: 'Sistema Teste',
        message: 'Este é um e-mail de teste para verificar a configuração do EmailJS.'
      };

      const response = await emailjs.send(
        this.serviceId,
        this.templateId,
        testParams
      );

      console.log('Teste de configuração bem-sucedido:', response);
      return true;
    } catch (error) {
      console.error('Erro no teste de configuração:', error);
      return false;
    }
  }
}

// Instância global
window.emailManager = new EmailManager();

// Instruções de configuração
console.log(`
=== CONFIGURAÇÃO DO EMAILJS ===
1. Crie uma conta em https://www.emailjs.com/
2. Configure um serviço de e-mail (Gmail, Outlook, etc.)
3. Crie um template de e-mail
4. Substitua as credenciais no arquivo email-manager.js:
   - YOUR_SERVICE_ID
   - YOUR_TEMPLATE_ID
   - YOUR_PUBLIC_KEY
5. Inclua o script do EmailJS no HTML
===============================`);