# Configuração do EmailJS para Sistema de Leads

## 1. Criar Conta no EmailJS

1. Acesse https://www.emailjs.com/
2. Crie uma conta gratuita
3. Confirme seu e-mail

## 2. Configurar Serviço de E-mail

1. No painel do EmailJS, vá em **Email Services**
2. Clique em **Add New Service**
3. Escolha seu provedor (Gmail, Outlook, etc.)
4. Configure as credenciais do seu e-mail
5. Anote o **Service ID** gerado

## 3. Criar Template para Cliente

1. Vá em **Email Templates**
2. Clique em **Create New Template**
3. Use o seguinte template:

### Template: Resultado da Simulação

**Subject:** Resultado da sua simulação de portabilidade - {{cliente_nome}}

**Content:**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #0B8F6C; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .result-box { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .positive { border-left: 5px solid #28a745; }
        .negative { border-left: 5px solid #dc3545; }
        .details { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        .btn { display: inline-block; padding: 12px 24px; background: #0B8F6C; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sinergia Energia</h1>
            <p>Resultado da sua Simulação de Portabilidade</p>
        </div>
        
        <div class="content">
            <h2>Olá, {{cliente_nome}}!</h2>
            
            <p>Obrigado por simular a portabilidade de energia conosco. Aqui estão os detalhes da sua simulação:</p>
            
            <div class="result-box {{#if elegivel}}positive{{else}}negative{{/if}}">
                <h3>{{#if elegivel}}🎉 Parabéns! Você é elegível para desconto!{{else}}❌ Não elegível para desconto{{/if}}</h3>
                
                <div class="details">
                    <p><strong>📍 Estado:</strong> {{estado}}</p>
                    <p><strong>⚡ Distribuidora:</strong> {{distribuidora}}</p>
                    <p><strong>📊 Consumo:</strong> {{consumo_kwh}} kWh</p>
                    {{#if elegivel}}
                    <p><strong>💰 Valor atual da conta:</strong> {{valor_conta}}</p>
                    <p><strong>🎯 Desconto:</strong> {{desconto_percentual}}%</p>
                    <p><strong>💵 Economia mensal:</strong> {{economia_mensal}}</p>
                    <p><strong>📈 Economia anual:</strong> {{economia_anual}}</p>
                    {{else}}
                    <p><strong>❓ Motivo:</strong> {{motivo}}</p>
                    {{/if}}
                </div>
                
                <p>{{mensagem_resultado}}</p>
            </div>
            
            <div style="text-align: center;">
                <a href="https://wa.me/5549988558025" class="btn">Falar com Consultor</a>
                <a href="#" class="btn">Nova Simulação</a>
            </div>
            
            <p><strong>Seus dados de contato:</strong></p>
            <ul>
                <li>📧 E-mail: {{cliente_email}}</li>
                <li>📱 WhatsApp: {{cliente_whatsapp}}</li>
            </ul>
            
            <p><em>Data da simulação: {{data_simulacao}} às {{hora_simulacao}}</em></p>
        </div>
        
        <div class="footer">
            <p>Sinergia Energia - Parceira Oficial IGreen</p>
            <p>Este e-mail foi enviado automaticamente. Não responda a este e-mail.</p>
        </div>
    </div>
</body>
</html>
```

4. Salve o template e anote o **Template ID**

## 4. Criar Template para Equipe Comercial

1. Crie um novo template com o nome **template_equipe_comercial**
2. Use o seguinte conteúdo:

### Template: Notificação para Equipe

**Subject:** {{subject}}

**Content:**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .lead-box { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .eligible { border-left: 5px solid #28a745; }
        .not-eligible { border-left: 5px solid #dc3545; }
        .details { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Novo Lead Capturado</h1>
            <p>Sistema de Simulação - Sinergia Energia</p>
        </div>
        
        <div class="content">
            <div class="lead-box {{#if lead_status}}eligible{{else}}not-eligible{{/if}}">
                <h2>{{lead_nome}} - {{lead_status}}</h2>
                
                <div class="details">
                    <h3>📋 Dados do Lead:</h3>
                    <p><strong>Nome:</strong> {{lead_nome}}</p>
                    <p><strong>E-mail:</strong> {{lead_email}}</p>
                    <p><strong>WhatsApp:</strong> {{lead_whatsapp}}</p>
                    <p><strong>Status:</strong> {{lead_status}}</p>
                </div>
                
                <div class="details">
                    <h3>⚡ Dados da Simulação:</h3>
                    <p><strong>Estado:</strong> {{simulacao_estado}}</p>
                    <p><strong>Distribuidora:</strong> {{simulacao_distribuidora}}</p>
                    <p><strong>Consumo:</strong> {{simulacao_consumo}} kWh</p>
                    <p><strong>Economia Estimada:</strong> {{simulacao_economia}}</p>
                    <p><strong>Desconto:</strong> {{simulacao_desconto}}%</p>
                </div>
                
                <p><strong>🕐 Data/Hora:</strong> {{data_lead}}</p>
            </div>
            
            <p><strong>Próximos passos:</strong></p>
            <ul>
                <li>Entrar em contato com o lead em até 24h</li>
                <li>Validar dados e interesse</li>
                <li>Agendar apresentação se elegível</li>
            </ul>
        </div>
    </div>
</body>
</html>
```

## 5. Configurar Credenciais no Sistema

1. Abra o arquivo `static/email-manager.js`
2. Substitua as seguintes variáveis:
   - `YOUR_SERVICE_ID` pelo Service ID do passo 2
   - `YOUR_TEMPLATE_ID` pelo Template ID do template do cliente
   - `YOUR_PUBLIC_KEY` pela Public Key da sua conta

3. Para encontrar a Public Key:
   - No painel do EmailJS, vá em **Account**
   - Copie a **Public Key**

## 6. Configurar E-mail da Equipe Comercial

1. No arquivo `static/email-manager.js`
2. Na função `notificarEquipeComercial`
3. Altere o e-mail `comercial@sinergia.com.br` para o e-mail real da equipe

## 7. Testar Configuração

1. Abra o console do navegador
2. Execute: `emailManager.testarConfiguracao()`
3. Verifique se não há erros

## 8. Exemplo de Configuração Final

```javascript
// No arquivo email-manager.js
this.serviceId = 'service_abc123';     // Seu Service ID
this.templateId = 'template_xyz789';   // Seu Template ID do cliente
this.publicKey = 'user_def456';        // Sua Public Key
```

## 9. Limites da Conta Gratuita

- 200 e-mails por mês
- Para mais e-mails, considere upgrade para plano pago

## 10. Troubleshooting

### Erro: "EmailJS não está carregado"
- Verifique se o script do EmailJS está incluído no HTML
- Verifique a conexão com a internet

### Erro: "Service ID inválido"
- Verifique se o Service ID está correto
- Verifique se o serviço está ativo no painel

### E-mails não chegam
- Verifique a caixa de spam
- Verifique se o template está correto
- Verifique os logs no console do navegador

---

**Importante:** Mantenha suas credenciais seguras e nunca as compartilhe publicamente.