# Sistema de Gerenciamento de Reabilitação

Sistema completo em Python/Flask para gerenciamento de clientes em centro de reabilitação.

## Funcionalidades

### Segurança
- ✅ Sistema de login com autenticação
- ✅ Senhas criptografadas com hash
- ✅ Sessões seguras
- ✅ Soft delete (dados não são perdidos)
- ✅ Auditoria completa de todas as ações

### Validações
- ✅ Validação completa de CPF
- ✅ Validação de email
- ✅ Máscaras de input para CPF e telefone
- ✅ Validação de datas (saída não pode ser antes da entrada)

### Funcionalidades Principais
- ✅ Cadastro de clientes com fichas de tratamento
- ✅ Gestão de medicamentos por ficha
- ✅ **Contatos de emergência/familiares por ficha**
- ✅ Busca e filtros avançados
- ✅ Paginação
- ✅ Exportação para CSV
- ✅ Geração de relatórios em PDF
- ✅ Histórico completo de tratamentos

### Performance
- ✅ Queries otimizadas
- ✅ Índices no banco de dados
- ✅ Conexões com pool

## Instalação

1. Instale as dependências:
\`\`\`bash
pip install flask reportlab
\`\`\`

2. Execute o sistema:
\`\`\`bash
python app.py
\`\`\`

3. Acesse no navegador:
\`\`\`
http://localhost:5000
\`\`\`

## Credenciais Padrão

**Usuário:** admin
**Senha:** admin123

## Estrutura do Banco de Dados

- **usuarios** - Usuários do sistema
- **clientes** - Dados cadastrais dos clientes
- **fichas** - Fichas de tratamento
- **contatos_emergencia** - Contatos de emergência/familiares por ficha
- **medicamentos** - Medicamentos por ficha
- **auditoria** - Log de todas as ações

## Contatos de Emergência

Cada ficha pode ter múltiplos contatos de emergência com:
- Nome completo
- Parentesco (mãe, pai, irmão, etc)
- Telefone principal
- Telefone secundário
- Email
- Endereço completo
- Observações

Isso permite que em caso de emergência, a equipe médica tenha acesso rápido aos contatos dos familiares do paciente.

## Melhorias Implementadas

1. **Autenticação segura** com login/logout
2. **Soft delete** - dados deletados não são perdidos
3. **Máscaras visuais** para CPF e telefone
4. **Validação avançada** de CPF e datas
5. **Contatos de emergência** para cada ficha
6. **Auditoria completa** de todas as ações
7. **Exportação** de dados em CSV
8. **Relatórios** em PDF
9. **Paginação** para listas grandes
10. **Interface moderna** e responsiva
