# Registo de Melhorias — Tesouraria

Análise global do projeto, organizada por área. Cada item tem uma prioridade sugerida (🔴 Alta / 🟡 Média / 🟢 Baixa) — mas a prioridade real depende do que tu quiseres atacar primeiro. Isto é um documento vivo: vamos риscando/atualizando à medida que formos implementando.

---

## 1. Segurança

### 🔴 Sessões sem possibilidade de revogação
Tokens JWT duram 30 dias por omissão e não há "logout" no servidor — só se limpa o `localStorage` no cliente. Se um token for roubado, continua válido até expirar. Nada a fazer com urgência num projeto pessoal, mas vale a pena decidir conscientemente: reduzir `TOKEN_DIAS`, ou introduzir uma tabela de sessões/blacklist para poder revogar tokens (ex.: ao mudar password, ao eliminar conta, ou manualmente).

### 🟡 Descrições de movimentos enviadas para a Groq (LLM externo)
A categorização automática envia a descrição do movimento bancário (que pode incluir nomes, referências, etc.) para uma API externa. Para uso pessoal é uma escolha razoável, mas vale a pena estares consciente disto — e talvez mencionar isto se algum dia os "amigos próximos" perguntarem "para onde vão os meus dados". Nada de errado tecnicamente, é só uma decisão de produto a tornar explícita (ex.: opção de desativar a categorização por LLM).

### 🟡 Rate limiting só nas rotas de autenticação
`/movimentos`, `/categorias`, `/contas`, etc. não têm limite de pedidos. Para um grupo fechado de utilizadores o risco é baixo, mas um limite básico (ex.: X pedidos/minuto por utilizador) protege contra bugs no frontend que disparem chamadas em loop, ou scraping acidental.

### 🟡 Registo revela se um email já existe
`/registro` devolve explicitamente "Email já registado" (400), enquanto `/esqueci-password` tem o cuidado deliberado de não revelar nada. É uma inconsistência a decidir conscientemente — muitas apps aceitam esta troca no registo, mas convém ser uma escolha e não um esquecimento.

### 🟢 Sem verificação de email no registo
Qualquer pessoa pode registar-se com qualquer email (não é validado que é dono dele). Para um grupo fechado pode nem ser prioritário, mas se abrires a app a mais gente, isto começa a importar.

### 🟢 `/docs` e `/redoc` do FastAPI ficam expostos por omissão
Não há problema nenhum para uso interno, mas se algum dia isto for exposto publicamente convém decidir se queres `docs_url=None` em produção.

### 🟢 CDNs sem Subresource Integrity (SRI)
`Chart.js` e `Litepicker` são carregados de CDN sem hash de integridade, e o Litepicker nem sequer tem versão fixa no URL (`.../dist/litepicker.js` sem número de versão — pode mudar de conteúdo sem aviso). Vale a pena fixar versões e considerar SRI, sobretudo porque o token fica em `localStorage` e é acessível a qualquer script que corra na página.

---

## 2. Arquitetura & Organização de Código

### 🟡 Muita repetição de gestão de ligação à BD
Praticamente todas as rotas repetem o padrão:
```python
conn = get_connection()
cursor = conn.cursor()
try:
    ...
finally:
    cursor.close()
    release_connection(conn)
```
Isto é propenso a esquecimentos (e já há sinais disso — ver ponto seguinte) e dificulta garantir rollback consistente em caso de erro. Uma dependency do FastAPI (`Depends(get_db)`) que devolve um cursor e trata commit/rollback/close automaticamente reduziria bastante este boilerplate e tornava o código mais seguro.

### 🟢 Imports duplicados de `release_connection`
Em vários ficheiros (`contas.py`, `movimentos.py`, `categorias.py`, `perfil.py`, `main.py`, `conftest.py`) o import está repetido — `from app.db.database import get_connection, release_connection, release_connection`. É inofensivo (Python ignora o duplicado) mas é sinal de copy-paste e vale a pena limpar — já agora, boa oportunidade para introduzir a dependency do ponto anterior e eliminar isto de vez.

### 🟡 Sem tratamento genérico de exceções não previstas
Só há handlers para `RequestValidationError` e `RateLimitExceeded`. Um erro inesperado (ex.: falha de ligação à BD a meio de uma transação) cai no handler por omissão do FastAPI — não há garantia de rollback da transação nem logging estruturado do erro do lado do servidor. Vale a pena um `exception_handler` genérico que faça log e devolva uma mensagem amigável.

### 🟢 Lógica de negócio misturada com SQL diretamente nas rotas
Funciona bem para o tamanho atual do projeto, mas rotas como `eliminar_categoria` (com toda a lógica de migração/cascata) ou `criar_movimento` (validações + insert + cache) já têm bastante lógica dentro do router. Não é urgente, mas se o projeto crescer, extrair para uma camada de "serviços" (como já fazes com `categorizacao.py` e `reconciliacoes.py`) facilita testar e reutilizar essa lógica fora do contexto HTTP.

### 🟢 Sem logging estruturado nem correlação de pedidos
Há `logging.basicConfig` básico, mas não há request-id para conseguires seguir um pedido específico nos logs quando algo correr mal.

---

## 3. Backend — Funcionalidades e Lógica

### 🔴 O serviço de categorização automática não está ligado à API
`app/services/categorizacao.py` (cache + LLM + fallback) só é usado em `scripts/importar.py`. Não existe nenhuma rota que receba movimentos "em bruto" (ex.: um extrato importado) e use `categorizar()` automaticamente — o `POST /movimentos` exige sempre `categoria_id` já definido pelo cliente. Ou seja, a funcionalidade de auto-categorização (que é claramente central ao projeto, dado o esforço posto nela e nos testes) só existe no script local. Se a intenção é os utilizadores importarem extratos bancários (CSV/Excel/etc.) diretamente na app, falta essa rota/fluxo end-to-end.

### 🟡 Cache de categorização é sensível a maiúsculas/espaços
`buscar_em_cache`/`guardar_em_cache` comparam a descrição por igualdade exata. Descrições reais de extratos bancários variam ligeiramente ao longo do tempo (espaços extra, referências que mudam, maiúsculas/minúsculas inconsistentes consoante o banco). Isto reduz a eficácia do cache — a mesma loja pode gerar várias entradas de cache diferentes. Vale a pena normalizar (upper/strip/colapsar espaços, talvez remover números de referência variáveis) antes de guardar/procurar.

### 🟡 Sem forma de importar extratos bancários pela app
Ligado ao ponto acima — atualmente a única forma de "importar" é o script `importar.py` a correr localmente contra `dados_mock.json`. Para uma app de gestão financeira, importar CSV/Excel do banco é provavelmente uma das funcionalidades mais valiosas a construir a seguir.

### 🟢 `errors.py` só reporta o primeiro erro de validação
Se vários campos falharem ao mesmo tempo, o utilizador só vê o erro do primeiro. Simples de resolver (agregar todos os erros), mas é uma escolha deliberada de simplicidade — só menciono para decidires conscientemente.

### 🟢 `/` não redireciona para a app
A raiz devolve `{"status": "ok", ...}` em vez de redirecionar para `/static/index.html`. Pequeno detalhe de conveniência.

---

## 4. Base de Dados

### 🟢 Índices parecem bem pensados
`idx_movimentos_conta`, `idx_movimentos_data`, `idx_movimentos_utilizador_data`, `idx_categorias_utilizador_parent` — cobrem bem os padrões de consulta mais comuns. Nada a mudar aqui para já.

### 🟢 `contas.id` e `movimentos.id` são `text` (UUIDs gerados em Python)
Funciona bem, só a notar que não há validação de formato UUID ao nível da BD — é inofensivo dado que é sempre gerado pela app, mas se algum dia aceitares IDs vindos de fora, vale a pena validar.

---

## 5. Frontend


### 🟡 Promises de `fetch` sem `.catch`
Erros de rede (sem ligação, timeout) não são apanhados em lado nenhum — resultam em unhandled promise rejections e partes da UI que ficam "penduradas" sem feedback ao utilizador.

### 🟡 Token em `localStorage`
Combinado com scripts de CDN sem SRI (ver secção 1), há uma superfície de ataque XSS teoricamente possível. Não é urgente para uso pessoal/familiar, mas é bom ter presente como trade-off consciente.

### 🟡 Ficheiro único de ~2500 linhas (HTML+CSS+JS inline)
Perfeitamente aceitável na fase atual, mas à medida que forem entrando mais funcionalidades vai custar cada vez mais a navegar e manter. Não é urgente mudar agora — mas se decidires investir tempo de aprendizagem nalguma ferramenta de frontend (mesmo sem framework completo, ex. Vite + módulos ES, ou dar o salto para Vue/Svelte), este é o sinal de que valeria a pena.

### 🟢 Botões não desativam durante pedidos assíncronos
Alguém com ligação lenta pode clicar "Guardar" várias vezes e disparar pedidos duplicados. Fácil de resolver com um `disabled = true` no início do pedido.

### 🟢 Sem debounce na pesquisa de movimentos
Não é um problema agora (a pesquisa é só filtragem local em `movimentosCache`, não faz pedidos à API), mas se algum dia passar a pesquisa no servidor, vai precisar de debounce.

---

## 6. Testes

De um modo geral, a suite de testes é bastante sólida — cobre bem casos limite (categorias protegidas, eliminação em cascata, reconciliações com datas intermédias, isolamento entre utilizadores). Pontos a considerar:

### 🟡 Falta um teste que confirme que o token de reset só pode ser usado uma vez
Diretamente relacionado com o bug de segurança da secção 1 — escrever este teste primeiro (e vê-lo falhar) é uma boa forma de guiar a correção.

### 🟢 Sem testes de frontend
Compreensível não haver testes de JS vanilla, mas se o frontend crescer vale a pena considerar testes E2E leves (ex. Playwright) para os fluxos críticos (login, criar movimento, eliminar conta).

### 🟢 `conftest.py` assume que `schema.sql` está sempre atualizado
Funciona bem enquanto o fluxo for "recriar do zero", mas volta a apontar para a necessidade de migrações — no dia em que a BD de testes e a de produção não puderem ser recriadas da mesma forma, este pressuposto quebra.

---

## 7. Desempenho

Nada crítico neste momento — os índices estão bem pensados para o volume atual. A registar para o futuro:

### 🟢 Sem paginação em `/movimentos`
Devolve sempre todos os movimentos do utilizador. Para uso pessoal/familiar ao longo de vários anos isto pode começar a pesar. Não é urgente, mas é bom ter no radar antes que se torne perceptível.

### 🟢 `/stats/saldo-diario` gera uma série temporal dia-a-dia × conta com subquery lateral
Correto e bem indexado, mas pode ficar mais pesado com períodos muito longos ou muitas contas. De novo, não é problema à escala atual.

---

## 8. UX / Produto

### 🟡 Sem forma de partilhar contas entre utilizadores
Disseste que o objetivo é uso pessoal e por um pequeno grupo de pessoas próximas — mas atualmente cada utilizador tem os seus dados completamente isolados (tudo filtrado por `utilizador_id`). Se a ideia for, por exemplo, um casal partilhar uma conta bancária conjunta na app, isso ainda não é possível. Vale a pena pensar se este é um requisito real do teu grupo de utilizadores ou se cada pessoa vai mesmo gerir só as suas próprias contas.

### 🟢 Sem exportação de dados (CSV/Excel)
Útil para relatórios pontuais ou para levar dados para outra ferramenta.

### 🟢 Sem orçamentos/limites por categoria
Uma funcionalidade natural para uma app de finanças pessoais — definir um limite mensal por categoria e ser avisado quando se aproxima/ultrapassa.

### 🟢 Sem PWA / instalável no telemóvel
Dado que o frontend já é responsivo, adicionar um `manifest.json` simples tornaria a app instalável no telemóvel com pouco esforço.

### 🟢 Sem modo escuro

---

## 9. Operações / Deployment

### 🟢 `docs_url`/`redoc_url` expostos por omissão
Ver secção 1 — a decidir consoante o plano de deployment.

### 🟢 Sem monitorização/alertas
Nada urgente para uso pessoal, mas se a app passar a ser usada por mais gente de forma regular, vale a pena ter alguma forma simples de saber se caiu (ex. um ping externo ao `/health`).

---

## Resumo — por onde eu sugeriria começar

Dado o teu contexto (uso pessoal + grupo próximo, projeto de aprendizagem), sugiro esta ordem de ataque:

1. **Migrações de BD** — antes de teres dados reais de outras pessoas, isto evita dores de cabeça mais tarde.
2. **Token de reset reutilizável** — correção de segurança pequena e concreta, boa para praticar TDD (escrever o teste que falha primeiro).
3. **`api()` não trata 401** — bug real, impacto direto na experiência quando o token expira.
4. **Ligação da categorização automática à API** — é o coração funcional do projeto e ainda não está acessível a utilizadores reais.
5. A partir daí, o resto é priorização tua consoante o que mais te interessa aprender ou o que mais falta faz ao uso diário.

Fico à disposição para começarmos por qualquer um destes pontos, ou por outro que prefiras.
