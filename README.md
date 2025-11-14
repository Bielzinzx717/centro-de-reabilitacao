# 🏥 Sistema de Centro de Reabilitação

Sistema CRUD completo desenvolvido em **Python** e **HTML puro** para gerenciamento de clientes de um centro de reabilitação.

## 📋 Funcionalidades

- ✅ Cadastro de clientes com validação de CPF e email
- ✅ Listagem de todos os clientes cadastrados
- ✅ Edição de dados dos clientes
- ✅ Exclusão de clientes
- ✅ Controle de data de entrada e saída da clínica
- ✅ Status visual (Em Tratamento / Finalizado)
- ✅ Banco de dados SQLite (sem necessidade de servidor externo)

## 🚀 Como Executar

### 1. Instalar Dependências

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Executar o Servidor

\`\`\`bash
python app.py
\`\`\`

### 3. Acessar o Sistema

Abra seu navegador e acesse: **http://localhost:5000**

## 📊 Dados Armazenados

- **Nome Completo**
- **CPF** (único, não pode ser duplicado)
- **Email**
- **Telefone**
- **Data de Entrada na Clínica**
- **Data de Saída da Clínica** (opcional)

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3 + Flask
- **Frontend**: HTML5 + CSS3 puro
- **Banco de Dados**: SQLite3
- **Validações**: CPF (11 dígitos) e Email (formato válido)

## 📱 Interface

- Design moderno e responsivo
- Gradiente roxo profissional
- Alertas de sucesso e erro
- Tabela com status visual dos pacientes
- Formulários com validação

## 🔒 Segurança

- Validação de CPF no backend
- Validação de email no backend
- Proteção contra CPFs duplicados
- Confirmação antes de excluir registros
