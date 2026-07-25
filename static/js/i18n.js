// ═══════════════════════════════════════════════════════════
// i18n — tradução do frontend (PT/EN)
// ═══════════════════════════════════════════════════════════
// Nada disto depende do backend: as mensagens de erro do backend continuam sempre em
// português (o contrato {code, message} já foi desenhado para isto — code é estável e sem
// língua, a tradução fica ao critério de quem apresenta o erro, ver ERROS_TRADUCOES em
// baixo). A preferência de língua fica em localStorage, tal como o tema — não faz parte do
// perfil do utilizador, é uma preferência do dispositivo/browser.
//
// Cobertura actual (ver analise-tesouraria.md): ecrã de autenticação, navegação principal
// (friso/avatar), Preferências, e as 4 páginas principais — Contas, Perfil, Movimentos e
// Análise — com os respectivos modais.

import { estadoGlobal } from './estado.js'

export const TRADUCOES = {
  pt: {
    // auth
    "auth.entrar": "Entrar",
    "auth.criar_conta": "Criar conta",
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.esqueci_password": "Esqueci a password",
    "auth.enviar_instrucoes": "Enviar instruções",
    "auth.voltar_a_entrar": "Voltar a entrar",
    "auth.nome": "Nome",
    "auth.password_minimo": "Mínimo de 8 caracteres.",
    "auth.nova_password": "Nova password",
    "auth.guardar_nova_password": "Guardar nova password",
    "auth.mostrar_password": "Mostrar password",
    "auth.ocultar_password": "Ocultar password",

    // navegação principal
    "friso.contas": "Contas",
    "friso.movimentos": "Movimentos",
    "friso.analise": "Análise",
    "friso.expandir_menu": "Expandir menu",
    "friso.recolher_menu": "Recolher menu",
    "friso.abrir_menu": "Abrir menu",
    "friso.adicionar": "Adicionar",
    "menu.ocultar_valores": "Ocultar valores",
    "menu.mostrar_valores": "Mostrar valores",
    "menu.configuracoes": "Configurações",
    "menu.terminar_sessao": "Terminar sessão",

    // perfil — navegação lateral + preferências
    "perfil.fechar": "Fechar",
    "perfil.sidebar.conta": "Conta",
    "perfil.sidebar.seguranca": "Segurança",
    "perfil.sidebar.categorias": "Categorias",
    "perfil.sidebar.preferencias": "Preferências",
    "perfil.preferencias.titulo": "Preferências",
    "perfil.preferencias.idioma": "Idioma",
    "perfil.preferencias.moeda": "Moeda Principal",
    "perfil.preferencias.moeda_valor": "Detetada automaticamente",
    "perfil.preferencias.aparencia": "Aparência",
    "tema.claro": "Claro",
    "tema.escuro": "Escuro",
    "tema.sistema": "Sistema",
    "lingua.pt": "Português",
    "lingua.en": "English",

    // genérico (usado em vários sítios — modais de confirmação, botões de formulário)
    "generico.cancelar": "Cancelar",
    "generico.guardar": "Guardar",

    "generico.confirmar": "Confirmar",
    "generico.editar": "Editar",
    "generico.eliminar": "Eliminar",
    "generico.entradas": "Entradas",
    "generico.saidas": "Saídas",
    "generico.entrada": "Entrada",
    "generico.saida": "Saída",
    "filtros.sem_banco": "Sem banco",
    "contas.menu.reconciliacoes": "Reconciliações",
    "movimentos.escolhe_primeiro_o_tipo": "Escolhe primeiro o Tipo",
    "erro.inesperado": "Ocorreu um erro inesperado.",
    "generico.a_carregar": "A carregar...",

    // perfil — secções Conta/Segurança/Categorias
    "perfil.conta.eliminar_conta": "Eliminar conta",
    "perfil.seguranca.palavra_passe": "Palavra-passe",
    "perfil.seguranca.terminar_sessoes": "Terminar sessão em todos os dispositivos",
    "perfil.categorias.adicionar_grupo": "+ Adicionar Grupo",
    "perfil.categorias.adicionar_categoria_aria": "Adicionar categoria",
    "perfil.categorias.mover_para_cima": "Mover para cima",
    "perfil.categorias.mover_para_baixo": "Mover para baixo",
    "perfil.categorias.sem_grupos_entradas": "Ainda não tens grupos de Entradas.",
    "perfil.categorias.sem_grupos_saidas": "Ainda não tens grupos de Saídas.",
    "perfil.categorias.grupo_protegido_ajuda": "Este grupo contém uma categoria necessária para o sistema e não pode ser eliminado.",
    "perfil.categorias.categoria_protegida_ajuda": "Categoria do sistema — não pode ser renomeada ou eliminada.",
    "perfil.msg.perfil_atualizado": "Perfil atualizado.",
    "perfil.msg.password_atualizada": "Password atualizada. As tuas outras sessões foram terminadas.",
    "perfil.msg.confirmar_terminar_sessoes": "Isto termina a tua sessão em todos os dispositivos, incluindo este. Vais precisar de voltar a entrar. Continuar?",
    "perfil.msg.sessoes_terminadas": "Sessões terminadas. Inicia sessão novamente.",
    "perfil.msg.confirmar_eliminar_conta_1": "Isto elimina PERMANENTEMENTE a tua conta e todos os dados. Tens a certeza?",
    "perfil.msg.confirmar_eliminar_conta_2": "Última confirmação — não há forma de recuperar isto depois. Continuar?",
    "perfil.msg.eliminar_definitivamente": "Eliminar definitivamente",

    // modal Editar Perfil / Alterar Password
    "modal_perfil.editar_titulo": "Editar perfil",
    "modal_perfil.alterar_password_titulo": "Alterar palavra-passe",
    "modal_perfil.password_atual": "Password Atual",
    "modal_perfil.atualizar_password": "Atualizar Password",

    // modal Grupo / Categoria (gestão)
    "modal_grupo.titulo_adicionar": "Adicionar grupo",
    "modal_grupo.titulo_editar": "Editar grupo",
    "modal_grupo.nome": "Nome",
    "modal_grupo.tipo": "Tipo",
    "modal_grupo.tipo_entrada": "Entrada (Recebimento)",
    "modal_grupo.tipo_saida": "Saída (Pagamento)",
    "modal_categoria.titulo_adicionar": "Adicionar categoria",
    "modal_categoria.titulo_editar": "Editar categoria",
    "modal_categoria.nome": "Nome",
    "modal_categoria.grupo": "Grupo",
    "modal_eliminar_cat.titulo_categoria": "Eliminar categoria",
    "modal_eliminar_cat.titulo_grupo": "Eliminar grupo",
    "modal_eliminar_cat.mover_para": "Mover para:",
    "modal_eliminar_cat.eliminar_sem_migrar": "Eliminar sem migrar",
    "modal_eliminar_cat.migrar_e_eliminar": "Migrar e eliminar",
    "modal_eliminar_cat.confirmar_forcar": "Isto vai eliminar também os movimentos associados, de forma permanente. Continuar?",

    // página Contas
    "contas.titulo": "Contas",
    "contas.adicionar": "Adicionar conta",
    "contas.filtros": "Filtros",
    "contas.filtro.contas_label": "Contas",
    "contas.filtro.todas": "Todas",
    "contas.filtro.pesquisar": "Pesquisar conta ou banco...",
    "contas.filtro.limpar_seccao": "Limpar Secção",
    "contas.filtro.concluir": "Concluir",
    "contas.filtro.limpar_filtros": "✕ Limpar Filtros",
    "contas.evolucao_saldo": "Evolução do Saldo",
    "contas.ordenar": "Ordenar",
    "contas.ordenar_por": "Ordenar por",
    "contas.direcao": "Direção",
    "contas.coluna.nome": "Nome",
    "contas.coluna.banco": "Banco",
    "contas.coluna.tipo": "Tipo",
    "contas.coluna.iban": "IBAN",
    "contas.coluna.inicio": "Data Início",
    "contas.coluna.saldo": "Saldo Atual",
    "contas.vazio.sem_contas": "Ainda não tens contas.",
    "contas.vazio.nenhuma_encontrada": "Nenhuma conta encontrada.",
    "contas.vazio.limpar_filtro": "Limpar filtro",
    "contas.acoes.mais_acoes": "Mais ações",
    "contas.acoes.reconciliacoes": "reconciliações",
    "contas.acoes.editar": "editar",
    "contas.acoes.eliminar": "Eliminar conta",
    "contas.confirmar_eliminar": "Eliminar esta conta?",
    "contas.confirmar_eliminar_com_movimentos": "Esta conta tem movimentos associados. Ao eliminar a conta, estes movimentos também serão eliminados. Continuar?",
    "contas.saldo_total": "Saldo Total",
    "contas.conta_ou_contas": "conta(s)",
    "contas.sem_dados_saldo": "Sem dados de saldo para mostrar.",
    "contas.adicionar_botao": "+ Adicionar Conta",
    "contas.confirmar_e_eliminar": "Confirmar e eliminar",
    "contas.eliminar_tudo": "Eliminar tudo",

    // modal Conta
    "modal_conta.titulo_adicionar": "Adicionar conta",
    "modal_conta.titulo_editar": "Editar conta",
    "modal_conta.nome": "Nome",
    "modal_conta.banco": "Banco",
    "modal_conta.tipo": "Tipo",
    "modal_conta.iban": "IBAN",
    "modal_conta.opcional": "(opcional)",
    "modal_conta.moeda": "Moeda",
    "modal_conta.data_inicio": "Data Início de Movimentos",
    "modal_conta.data_inicio_ajuda": "Dia a partir do qual vais registar movimentos desta conta no sistema.",
    "modal_conta.saldo_inicial": "Saldo Inicial",
    "modal_conta.saldo_inicial_ajuda": "Saldo da conta nesse dia, antes de começares a registar movimentos.",

    // modal Reconciliações
    "modal_reconc.titulo": "Reconciliações de Saldo",
    "modal_reconc.titulo_ajuda": "Uma reconciliação permite corrigir o saldo de uma conta numa data específica, sempre que o saldo real seja diferente do saldo apresentado na aplicação. Ao definir uma reconciliação, o saldo da conta é ajustado para o valor indicado na data especificada.",
    "modal_reconc.coluna_data": "Data",
    "modal_reconc.coluna_saldo_anterior": "Saldo Anterior",
    "modal_reconc.coluna_saldo_reconciliado": "Saldo Reconciliado",
    "modal_reconc.data_reconciliacao": "Data de Reconciliação",
    "modal_reconc.data_reconciliacao_ajuda": "Dia em que registas esta reconciliação, já depois de todos os movimentos desse dia.",
    "modal_reconc.saldo_reconciliado": "Saldo Reconciliado",
    "modal_reconc.saldo_reconciliado_ajuda": "Saldo da conta nesse dia, depois de todos os movimentos já ocorridos.",
    "modal_reconc.adicionar": "+ Adicionar reconciliação",
    "modal_reconc.vazio": "Nenhuma correção realizada.",
    "modal_reconc.confirmar_eliminar": "Eliminar esta reconciliação?",
    "modal_reconc.eliminar_aria": "Eliminar reconciliação",
    "modal_reconc.saldo_calculado_prefixo": "Saldo atual calculado nesta data:",

    // página Movimentos
    "movimentos.adicionar": "Adicionar movimento",
    "movimentos.filtro.categorias_label": "Categorias",
    "movimentos.filtro.pesquisar_categoria": "Pesquisar categoria...",
    "movimentos.periodo": "Período",
    "generico.selecionar_datas": "Selecionar datas",
    "generico.selecionar_data": "Selecionar data",
    "movimentos.pesquisar_descricao": "Pesquisar descrição...",
    "movimentos.coluna.data": "Data",
    "movimentos.coluna.descricao": "Descrição",
    "movimentos.coluna.conta": "Conta",
    "movimentos.coluna.categoria": "Categoria",
    "movimentos.coluna.valor": "Valor",
    "movimentos.vazio.nenhum_encontrado": "Nenhum movimento encontrado.",
    "movimentos.vazio.limpar_filtros": "Limpar filtros",
    "movimentos.vazio.sem_movimentos": "Ainda não tens movimentos.",
    "movimentos.vazio.adicionar": "+ Adicionar",
    "movimentos.confirmar": "confirmar",
    "movimentos.eliminar_aria": "Eliminar movimento",
    "movimentos.confirmar_eliminar": "Eliminar este movimento?",
    "movimentos.pendentes.a_mostrar_so_pendentes": "A mostrar apenas movimentos pendentes de confirmação.",
    "movimentos.pendentes.confirmar_todos": "Confirmar todos",
    "movimentos.pendentes.ver_todos": "Ver todos",
    "movimentos.pendentes.ajuda": "Os movimentos são categorizados automaticamente através de um sistema que recorre à Inteligência Artificial. A categorização pode não ser correta em alguns casos, por isso recomenda-se a validação das categorias atribuídas.",
    "movimentos.pendentes.contagem_texto": "movimento(s) categorizados pelo sistema.",
    "movimentos.pendentes.ver_pendentes": "Ver pendentes",
    "movimentos.pendentes.confirmar_todos_pergunta": "Confirmar todos os movimentos categorizados automaticamente?",

    // modal Movimento
    "modal_movimento.titulo_adicionar": "Adicionar movimento",
    "modal_movimento.titulo_editar": "Editar movimento",
    "modal_movimento.conta": "Conta",
    "modal_movimento.data": "Data",
    "modal_movimento.descricao": "Descrição",
    "modal_movimento.tipo": "Tipo",
    "modal_movimento.valor": "Valor",

    // página Análise
    "analise.aba.resumo": "Resumo",
    "analise.aba.recorrencias": "Saídas Recorrentes",
    "analise.evolucao_mensal": "Evolução Mensal",
    "analise.categorias": "Categorias",
    "analise.total": "Total",
    "analise.por_categoria": "Por categoria",
    "analise.sem_dados_periodo": "Sem dados para este período.",
    "analise.coluna.valor_medio": "Valor Médio",
    "analise.coluna.frequencia": "Frequência",
    "analise.coluna.proxima_data": "Próxima Data Estimada",
    "analise.liquido": "Líquido",
    "analise.das_entradas": "das entradas",
    "analise.grafico_vazio": "Sem movimentos para analisar.",
    "analise.mes_anterior": "mês anterior",
    "analise.sem_resultados_filtros": "Nenhum resultado com os filtros atuais.",
    "analise.sem_entradas_para_analisar": "Sem entradas para analisar.",
    "analise.sem_saidas_para_analisar": "Sem saídas para analisar.",
    "analise.ver_evolucao_mensal_de": "Ver evolução mensal de",
    "analise.recolher_todos_grupos": "Recolher todos os grupos",
    "analise.expandir_todos_grupos": "Expandir todos os grupos",
    "analise.recorrentes.sem_resultado": "Nenhum resultado encontrado.",
    "analise.recorrentes.sem_dados": "Nenhum padrão recorrente detetado.",
    "analise.dias_sufixo": "dias",
    "analise.irregular_sufixo": "(irregular)",
    "analise.do_grupo": "do grupo",

    // calendário
    "calendario.mes_anterior": "Mês anterior",
    "calendario.mes_seguinte": "Mês seguinte",
    "calendario.mes_aria": "Mês",
    "calendario.ano_aria": "Ano",
    "calendario.preset.este_mes": "Este mês",
    "calendario.preset.mes_passado": "Mês passado",
    "calendario.preset.30_dias": "30 dias",
    "calendario.preset.este_ano": "Este ano",
    "calendario.preset.ano_passado": "Ano passado",
    "calendario.preset.365_dias": "365 dias",
    "calendario.escolhe_data_inicio": "Escolhe a data de início",
    "calendario.escolhe_fim": "escolhe o fim",

    // ordenação (painéis "Ordenar" de Contas/Movimentos/Análise-Recorrentes)
    "ordenar.prefixo_botao": "Ordenar: ",
    "ordenar.nome": "Nome",
    "ordenar.saldo_atual": "Saldo Atual",
    "ordenar.data_inicio": "Data Início",
    "ordenar.data": "Data",
    "ordenar.valor": "Valor",
    "ordenar.descricao": "Descrição",
    "ordenar.valor_medio": "Valor Médio",
    "ordenar.frequencia": "Frequência",
    "ordenar.proxima_data": "Próxima Data",
    "ordenar.a_z": "A → Z",
    "ordenar.z_a": "Z → A",
    "ordenar.maior_menor": "Maior → Menor",
    "ordenar.menor_maior": "Menor → Maior",
    "ordenar.antigo_recente": "Antigo → Recente",
    "ordenar.recente_antigo": "Recente → Antigo",
    "ordenar.frequente_raro": "Frequente → Raro",
    "ordenar.raro_frequente": "Raro → Frequente",
    "ordenar.proximo_distante": "Próximo → Distante",
    "ordenar.distante_proximo": "Distante → Próximo",

    // toasts genéricos (sessão/rede) e auth
    "toast.sem_ligacao_servidor": "Não foi possível ligar ao servidor.",
    "toast.sessao_expirou": "A tua sessão expirou. Inicia sessão novamente.",
    "toast.sessao_terminada_inatividade": "Sessão terminada por inatividade.",
    "auth.esqueci_password_confirmacao": "Se o email existir, enviámos instruções.",
    "auth.password_redefinida": "Password redefinida com sucesso. Já podes entrar.",
  },
  en: {
    "auth.entrar": "Log in",
    "auth.criar_conta": "Create account",
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.esqueci_password": "Forgot password",
    "auth.enviar_instrucoes": "Send instructions",
    "auth.voltar_a_entrar": "Back to login",
    "auth.nome": "Name",
    "auth.password_minimo": "At least 8 characters.",
    "auth.nova_password": "New password",
    "auth.guardar_nova_password": "Save new password",
    "auth.mostrar_password": "Show password",
    "auth.ocultar_password": "Hide password",

    "friso.contas": "Accounts",
    "friso.movimentos": "Transactions",
    "friso.analise": "Analysis",
    "friso.expandir_menu": "Expand menu",
    "friso.recolher_menu": "Collapse menu",
    "friso.abrir_menu": "Open menu",
    "friso.adicionar": "Add",
    "menu.ocultar_valores": "Hide amounts",
    "menu.mostrar_valores": "Show amounts",
    "menu.configuracoes": "Settings",
    "menu.terminar_sessao": "Log out",

    "perfil.fechar": "Close",
    "perfil.sidebar.conta": "Account",
    "perfil.sidebar.seguranca": "Security",
    "perfil.sidebar.categorias": "Categories",
    "perfil.sidebar.preferencias": "Preferences",
    "perfil.preferencias.titulo": "Preferences",
    "perfil.preferencias.idioma": "Language",
    "perfil.preferencias.moeda": "Main Currency",
    "perfil.preferencias.moeda_valor": "Auto-detected",
    "perfil.preferencias.aparencia": "Appearance",
    "tema.claro": "Light",
    "tema.escuro": "Dark",
    "tema.sistema": "System",
    "lingua.pt": "Português",
    "lingua.en": "English",

    "generico.cancelar": "Cancel",
    "generico.guardar": "Save",
    "generico.confirmar": "Confirm",
    "generico.editar": "Edit",
    "generico.eliminar": "Delete",
    "generico.entradas": "Income",
    "generico.saidas": "Expenses",
    "generico.entrada": "Income",
    "generico.saida": "Expense",
    "filtros.sem_banco": "No bank",
    "contas.menu.reconciliacoes": "Reconciliations",
    "movimentos.escolhe_primeiro_o_tipo": "Choose the Type first",
    "erro.inesperado": "An unexpected error occurred.",
    "generico.a_carregar": "Loading...",

    "perfil.conta.eliminar_conta": "Delete account",
    "perfil.seguranca.palavra_passe": "Password",
    "perfil.seguranca.terminar_sessoes": "Log out of all devices",
    "perfil.categorias.adicionar_grupo": "+ Add Group",
    "perfil.categorias.adicionar_categoria_aria": "Add category",
    "perfil.categorias.mover_para_cima": "Move up",
    "perfil.categorias.mover_para_baixo": "Move down",
    "perfil.categorias.sem_grupos_entradas": "You don't have any Income groups yet.",
    "perfil.categorias.sem_grupos_saidas": "You don't have any Expense groups yet.",
    "perfil.categorias.grupo_protegido_ajuda": "This group contains a category required by the system and cannot be deleted.",
    "perfil.categorias.categoria_protegida_ajuda": "System category — cannot be renamed or deleted.",
    "perfil.msg.perfil_atualizado": "Profile updated.",
    "perfil.msg.password_atualizada": "Password updated. Your other sessions have been logged out.",
    "perfil.msg.confirmar_terminar_sessoes": "This will log you out on all devices, including this one. You'll need to log in again. Continue?",
    "perfil.msg.sessoes_terminadas": "Sessions logged out. Please log in again.",
    "perfil.msg.confirmar_eliminar_conta_1": "This PERMANENTLY deletes your account and all data. Are you sure?",
    "perfil.msg.confirmar_eliminar_conta_2": "Final confirmation — there's no way to undo this afterwards. Continue?",
    "perfil.msg.eliminar_definitivamente": "Delete permanently",

    "modal_perfil.editar_titulo": "Edit profile",
    "modal_perfil.alterar_password_titulo": "Change password",
    "modal_perfil.password_atual": "Current Password",
    "modal_perfil.atualizar_password": "Update Password",

    "modal_grupo.titulo_adicionar": "Add group",
    "modal_grupo.titulo_editar": "Edit group",
    "modal_grupo.nome": "Name",
    "modal_grupo.tipo": "Type",
    "modal_grupo.tipo_entrada": "Income",
    "modal_grupo.tipo_saida": "Expense",
    "modal_categoria.titulo_adicionar": "Add category",
    "modal_categoria.titulo_editar": "Edit category",
    "modal_categoria.nome": "Name",
    "modal_categoria.grupo": "Group",
    "modal_eliminar_cat.titulo_categoria": "Delete category",
    "modal_eliminar_cat.titulo_grupo": "Delete group",
    "modal_eliminar_cat.mover_para": "Move to:",
    "modal_eliminar_cat.eliminar_sem_migrar": "Delete without moving",
    "modal_eliminar_cat.migrar_e_eliminar": "Move and delete",
    "modal_eliminar_cat.confirmar_forcar": "This will also permanently delete the associated transactions. Continue?",

    "contas.titulo": "Accounts",
    "contas.adicionar": "Add account",
    "contas.filtros": "Filters",
    "contas.filtro.contas_label": "Accounts",
    "contas.filtro.todas": "All",
    "contas.filtro.pesquisar": "Search account or bank...",
    "contas.filtro.limpar_seccao": "Clear Section",
    "contas.filtro.concluir": "Done",
    "contas.filtro.limpar_filtros": "✕ Clear Filters",
    "contas.evolucao_saldo": "Balance Over Time",
    "contas.ordenar": "Sort",
    "contas.ordenar_por": "Sort by",
    "contas.direcao": "Direction",
    "contas.coluna.nome": "Name",
    "contas.coluna.banco": "Bank",
    "contas.coluna.tipo": "Type",
    "contas.coluna.iban": "IBAN",
    "contas.coluna.inicio": "Start Date",
    "contas.coluna.saldo": "Current Balance",
    "contas.vazio.sem_contas": "You don't have any accounts yet.",
    "contas.vazio.nenhuma_encontrada": "No accounts found.",
    "contas.vazio.limpar_filtro": "Clear filter",
    "contas.acoes.mais_acoes": "More actions",
    "contas.acoes.reconciliacoes": "reconciliations",
    "contas.acoes.editar": "edit",
    "contas.acoes.eliminar": "Delete account",
    "contas.confirmar_eliminar": "Delete this account?",
    "contas.confirmar_eliminar_com_movimentos": "This account has associated transactions. Deleting the account will also delete these transactions. Continue?",
    "contas.saldo_total": "Total Balance",
    "contas.conta_ou_contas": "account(s)",
    "contas.sem_dados_saldo": "No balance data to show.",
    "contas.adicionar_botao": "+ Add Account",
    "contas.confirmar_e_eliminar": "Confirm and delete",
    "contas.eliminar_tudo": "Delete everything",

    "modal_conta.titulo_adicionar": "Add account",
    "modal_conta.titulo_editar": "Edit account",
    "modal_conta.nome": "Name",
    "modal_conta.banco": "Bank",
    "modal_conta.tipo": "Type",
    "modal_conta.iban": "IBAN",
    "modal_conta.opcional": "(optional)",
    "modal_conta.moeda": "Currency",
    "modal_conta.data_inicio": "Transaction Start Date",
    "modal_conta.data_inicio_ajuda": "The day from which you'll start recording transactions for this account.",
    "modal_conta.saldo_inicial": "Initial Balance",
    "modal_conta.saldo_inicial_ajuda": "The account's balance on that day, before you start recording transactions.",

    "modal_reconc.titulo": "Balance Reconciliations",
    "modal_reconc.titulo_ajuda": "A reconciliation lets you correct an account's balance on a specific date, whenever the real balance differs from the one shown in the app. Setting a reconciliation adjusts the account's balance to the given value on that date.",
    "modal_reconc.coluna_data": "Date",
    "modal_reconc.coluna_saldo_anterior": "Previous Balance",
    "modal_reconc.coluna_saldo_reconciliado": "Reconciled Balance",
    "modal_reconc.data_reconciliacao": "Reconciliation Date",
    "modal_reconc.data_reconciliacao_ajuda": "The day you're recording this reconciliation for, after all of that day's transactions.",
    "modal_reconc.saldo_reconciliado": "Reconciled Balance",
    "modal_reconc.saldo_reconciliado_ajuda": "The account's balance on that day, after all transactions that had already occurred.",
    "modal_reconc.adicionar": "+ Add reconciliation",
    "modal_reconc.vazio": "No correction made yet.",
    "modal_reconc.confirmar_eliminar": "Delete this reconciliation?",
    "modal_reconc.eliminar_aria": "Delete reconciliation",
    "modal_reconc.saldo_calculado_prefixo": "Current calculated balance on this date:",

    "movimentos.adicionar": "Add transaction",
    "movimentos.filtro.categorias_label": "Categories",
    "movimentos.filtro.pesquisar_categoria": "Search category...",
    "movimentos.periodo": "Period",
    "generico.selecionar_datas": "Select dates",
    "generico.selecionar_data": "Select date",
    "movimentos.pesquisar_descricao": "Search description...",
    "movimentos.coluna.data": "Date",
    "movimentos.coluna.descricao": "Description",
    "movimentos.coluna.conta": "Account",
    "movimentos.coluna.categoria": "Category",
    "movimentos.coluna.valor": "Amount",
    "movimentos.vazio.nenhum_encontrado": "No transactions found.",
    "movimentos.vazio.limpar_filtros": "Clear filters",
    "movimentos.vazio.sem_movimentos": "You don't have any transactions yet.",
    "movimentos.vazio.adicionar": "+ Add",
    "movimentos.confirmar": "confirm",
    "movimentos.eliminar_aria": "Delete transaction",
    "movimentos.confirmar_eliminar": "Delete this transaction?",
    "movimentos.pendentes.a_mostrar_so_pendentes": "Showing only transactions pending confirmation.",
    "movimentos.pendentes.confirmar_todos": "Confirm all",
    "movimentos.pendentes.ver_todos": "View all",
    "movimentos.pendentes.ajuda": "Transactions are automatically categorized by a system that uses Artificial Intelligence. The categorization may not always be correct, so reviewing the assigned categories is recommended.",
    "movimentos.pendentes.contagem_texto": "transaction(s) automatically categorized.",
    "movimentos.pendentes.ver_pendentes": "View pending",
    "movimentos.pendentes.confirmar_todos_pergunta": "Confirm all automatically categorized transactions?",

    "modal_movimento.titulo_adicionar": "Add transaction",
    "modal_movimento.titulo_editar": "Edit transaction",
    "modal_movimento.conta": "Account",
    "modal_movimento.data": "Date",
    "modal_movimento.descricao": "Description",
    "modal_movimento.tipo": "Type",
    "modal_movimento.valor": "Amount",

    "analise.aba.resumo": "Summary",
    "analise.aba.recorrencias": "Recurring Expenses",
    "analise.evolucao_mensal": "Monthly Trend",
    "analise.categorias": "Categories",
    "analise.total": "Total",
    "analise.por_categoria": "By category",
    "analise.sem_dados_periodo": "No data for this period.",
    "analise.coluna.valor_medio": "Average Amount",
    "analise.coluna.frequencia": "Frequency",
    "analise.coluna.proxima_data": "Estimated Next Date",
    "analise.liquido": "Net",
    "analise.das_entradas": "of income",
    "analise.grafico_vazio": "No transactions to analyze.",
    "analise.mes_anterior": "previous month",
    "analise.sem_resultados_filtros": "No results with the current filters.",
    "analise.sem_entradas_para_analisar": "No income to analyze.",
    "analise.sem_saidas_para_analisar": "No expenses to analyze.",
    "analise.ver_evolucao_mensal_de": "View monthly trend for",
    "analise.recolher_todos_grupos": "Collapse all groups",
    "analise.expandir_todos_grupos": "Expand all groups",
    "analise.recorrentes.sem_resultado": "No results found.",
    "analise.recorrentes.sem_dados": "No recurring pattern detected.",
    "analise.dias_sufixo": "days",
    "analise.irregular_sufixo": "(irregular)",
    "analise.do_grupo": "of the group",

    "calendario.mes_anterior": "Previous month",
    "calendario.mes_seguinte": "Next month",
    "calendario.mes_aria": "Month",
    "calendario.ano_aria": "Year",
    "calendario.preset.este_mes": "This month",
    "calendario.preset.mes_passado": "Last month",
    "calendario.preset.30_dias": "30 days",
    "calendario.preset.este_ano": "This year",
    "calendario.preset.ano_passado": "Last year",
    "calendario.preset.365_dias": "365 days",
    "calendario.escolhe_data_inicio": "Choose the start date",
    "calendario.escolhe_fim": "choose the end date",

    "ordenar.prefixo_botao": "Sort: ",
    "ordenar.nome": "Name",
    "ordenar.saldo_atual": "Current Balance",
    "ordenar.data_inicio": "Start Date",
    "ordenar.data": "Date",
    "ordenar.valor": "Amount",
    "ordenar.descricao": "Description",
    "ordenar.valor_medio": "Average Amount",
    "ordenar.frequencia": "Frequency",
    "ordenar.proxima_data": "Next Date",
    "ordenar.a_z": "A → Z",
    "ordenar.z_a": "Z → A",
    "ordenar.maior_menor": "Highest → Lowest",
    "ordenar.menor_maior": "Lowest → Highest",
    "ordenar.antigo_recente": "Oldest → Newest",
    "ordenar.recente_antigo": "Newest → Oldest",
    "ordenar.frequente_raro": "Frequent → Rare",
    "ordenar.raro_frequente": "Rare → Frequent",
    "ordenar.proximo_distante": "Soonest → Furthest",
    "ordenar.distante_proximo": "Furthest → Soonest",

    "toast.sem_ligacao_servidor": "Could not connect to the server.",
    "toast.sessao_expirou": "Your session has expired. Please log in again.",
    "toast.sessao_terminada_inatividade": "Session ended due to inactivity.",
    "auth.esqueci_password_confirmacao": "If that email exists, we've sent instructions.",
    "auth.password_redefinida": "Password reset successfully. You can now log in.",
  },
}

// Tradução dos nomes das categorias por omissão (slug -> nome, ver migração
// 0014_slug_categorias.sql e services/categorias_seed.py::ARVORE_PADRAO) — usado por
// nomeCategoria() em baixo. Categorias criadas pelo próprio utilizador não têm slug
// (ficam sempre como foram escritas, nunca traduzidas).
//
// `pt` aqui não é para mostrar (em português mostra-se sempre o `nome` guardado, editado
// ou não) — serve só para nomeCategoria() detectar se uma categoria por omissão ainda
// tem o nome original de fábrica. Se o utilizador a renomear para outra coisa qualquer
// (ex. "Supermercado" -> "Sítio aleatório"), o nome deixa de bater certo com este texto
// e a tradução automática pára — mostra o texto editado tal como está, nas duas línguas,
// em vez de continuar a mostrar "Supermarket" sem ligação nenhuma ao que lá está escrito.
// Gerado a partir de app/services/categorias_seed.py::ARVORE_PADRAO (mesma fonte que gera
// os slugs) para nunca divergir à mão.
export const CATEGORIAS_TRADUCOES = {
  pt: {
    "in.trabalho": "Trabalho",
    "in.investimentos": "Investimentos",
    "in.venda_de_ativos": "Venda de Ativos",
    "in.emprestimos": "Empréstimos",
    "in.transferencias_proprias": "Transferências Próprias",
    "in.outros_recebimentos": "Outros Recebimentos",
    "out.habitacao": "Habitação",
    "out.alimentacao": "Alimentação",
    "out.transportes": "Transportes",
    "out.educacao": "Educação",
    "out.saude_e_auto_cuidado": "Saúde e Auto-Cuidado",
    "out.entretenimento": "Entretenimento",
    "out.tecnologia": "Tecnologia",
    "out.impostos": "Impostos",
    "out.seguros": "Seguros",
    "out.servicos_financeiros": "Serviços Financeiros",
    "out.compra_de_ativos_para_investimento": "Compra de Ativos (para Investimento)",
    "out.transferencias_proprias": "Transferências Próprias",
    "out.outros_pagamentos": "Outros Pagamentos",

    "in.trabalho.salario": "Salário",
    "in.trabalho.premios": "Prémios",
    "in.trabalho.recibos_verdes": "Recibos Verdes",
    "in.trabalho.outros": "Outros",
    "in.investimentos.renda_de_imoveis": "Renda de Imóveis",
    "in.investimentos.dividendos": "Dividendos",
    "in.investimentos.juros": "Juros",
    "in.investimentos.outros": "Outros",
    "in.venda_de_ativos.imoveis": "Imóveis",
    "in.venda_de_ativos.veiculos": "Veículos",
    "in.venda_de_ativos.equipamentos": "Equipamentos",
    "in.venda_de_ativos.ativos_financeiros": "Ativos Financeiros",
    "in.venda_de_ativos.outros": "Outros",
    "in.emprestimos.credito_pessoal": "Crédito Pessoal",
    "in.emprestimos.emprestimo_particular": "Empréstimo Particular",
    "in.emprestimos.outros": "Outros",
    "in.transferencias_proprias.entre_contas": "Entre Contas",
    "in.transferencias_proprias.deposito_em_numerario": "Depósito em Numerário",
    "in.transferencias_proprias.outros": "Outros",
    "in.outros_recebimentos.reembolsos": "Reembolsos",
    "in.outros_recebimentos.presentes": "Presentes",
    "in.outros_recebimentos.donativos": "Donativos",
    "in.outros_recebimentos.herancas": "Heranças",
    "in.outros_recebimentos.outros": "Outros",
    "out.habitacao.prestacao": "Prestação",
    "out.habitacao.renda": "Renda",
    "out.habitacao.agua_eletricidade_e_gas": "Água, Eletricidade e Gás",
    "out.habitacao.telecomunicacoes": "Telecomunicações",
    "out.habitacao.bens_mobiliarios": "Bens Mobiliários",
    "out.habitacao.seguranca": "Segurança",
    "out.habitacao.condominio": "Condomínio",
    "out.habitacao.servicos_domesticos": "Serviços Domésticos",
    "out.habitacao.outros": "Outros",
    "out.alimentacao.supermercado": "Supermercado",
    "out.alimentacao.restaurantes_e_cafes": "Restaurantes e Cafés",
    "out.alimentacao.outros": "Outros",
    "out.transportes.prestacao": "Prestação",
    "out.transportes.combustivel": "Combustível",
    "out.transportes.manutencao_e_inspecao": "Manutenção e Inspeção",
    "out.transportes.portagens_e_estacionamento": "Portagens e Estacionamento",
    "out.transportes.transportes_publicos_e_tvde": "Transportes Públicos e TVDE",
    "out.transportes.outros": "Outros",
    "out.educacao.cursos_e_formacoes": "Cursos e Formações",
    "out.educacao.livros_e_material": "Livros e Material",
    "out.educacao.outros": "Outros",
    "out.saude_e_auto_cuidado.consultas_e_exames": "Consultas e Exames",
    "out.saude_e_auto_cuidado.tratamentos_e_medicamentos": "Tratamentos e Medicamentos",
    "out.saude_e_auto_cuidado.servicos_de_bem_estar": "Serviços de Bem-Estar",
    "out.saude_e_auto_cuidado.outros": "Outros",
    "out.entretenimento.viagens": "Viagens",
    "out.entretenimento.eventos": "Eventos",
    "out.entretenimento.subscricoes": "Subscrições",
    "out.entretenimento.outros": "Outros",
    "out.tecnologia.hardware": "Hardware",
    "out.tecnologia.software": "Software",
    "out.tecnologia.outros": "Outros",
    "out.impostos.irs": "IRS",
    "out.impostos.iuc": "IUC",
    "out.impostos.imi": "IMI",
    "out.impostos.coimas": "Coimas",
    "out.impostos.outros": "Outros",
    "out.seguros.habitacao": "Habitação",
    "out.seguros.automovel": "Automóvel",
    "out.seguros.saude": "Saúde",
    "out.seguros.vida": "Vida",
    "out.seguros.outros": "Outros",
    "out.servicos_financeiros.juros": "Juros",
    "out.servicos_financeiros.comissoes": "Comissões",
    "out.servicos_financeiros.outros": "Outros",
    "out.compra_de_ativos_para_investimento.imoveis": "Imóveis",
    "out.compra_de_ativos_para_investimento.veiculos": "Veículos",
    "out.compra_de_ativos_para_investimento.equipamentos": "Equipamentos",
    "out.compra_de_ativos_para_investimento.ativos_financeiros": "Ativos Financeiros",
    "out.compra_de_ativos_para_investimento.outros": "Outros",
    "out.transferencias_proprias.entre_contas": "Entre Contas",
    "out.transferencias_proprias.levantamento_em_numerario": "Levantamento em Numerário",
    "out.transferencias_proprias.outros": "Outros",
    "out.outros_pagamentos.presentes": "Presentes",
    "out.outros_pagamentos.donativos": "Donativos",
    "out.outros_pagamentos.quotas": "Quotas",
    "out.outros_pagamentos.outros": "Outros",
  },
  en: {
    // grupos — entradas
    "in.trabalho": "Work",
    "in.investimentos": "Investments",
    "in.venda_de_ativos": "Asset Sales",
    "in.emprestimos": "Loans",
    "in.transferencias_proprias": "Own Transfers",
    "in.outros_recebimentos": "Other Income",
    // grupos — saídas
    "out.habitacao": "Housing",
    "out.alimentacao": "Food",
    "out.transportes": "Transportation",
    "out.educacao": "Education",
    "out.saude_e_auto_cuidado": "Health & Self-Care",
    "out.entretenimento": "Entertainment",
    "out.tecnologia": "Technology",
    "out.impostos": "Taxes",
    "out.seguros": "Insurance",
    "out.servicos_financeiros": "Financial Services",
    "out.compra_de_ativos_para_investimento": "Asset Purchases (for Investment)",
    "out.transferencias_proprias": "Own Transfers",
    "out.outros_pagamentos": "Other Payments",

    // categorias-folha — Trabalho
    "in.trabalho.salario": "Salary",
    "in.trabalho.premios": "Bonuses",
    "in.trabalho.recibos_verdes": "Freelance Income",
    "in.trabalho.outros": "Other",
    // Investimentos
    "in.investimentos.renda_de_imoveis": "Rental Income",
    "in.investimentos.dividendos": "Dividends",
    "in.investimentos.juros": "Interest",
    "in.investimentos.outros": "Other",
    // Venda de Ativos
    "in.venda_de_ativos.imoveis": "Real Estate",
    "in.venda_de_ativos.veiculos": "Vehicles",
    "in.venda_de_ativos.equipamentos": "Equipment",
    "in.venda_de_ativos.ativos_financeiros": "Financial Assets",
    "in.venda_de_ativos.outros": "Other",
    // Empréstimos
    "in.emprestimos.credito_pessoal": "Personal Loan",
    "in.emprestimos.emprestimo_particular": "Private Loan",
    "in.emprestimos.outros": "Other",
    // Transferências Próprias (entradas)
    "in.transferencias_proprias.entre_contas": "Between Accounts",
    "in.transferencias_proprias.deposito_em_numerario": "Cash Deposit",
    "in.transferencias_proprias.outros": "Other",
    // Outros Recebimentos
    "in.outros_recebimentos.reembolsos": "Refunds",
    "in.outros_recebimentos.presentes": "Gifts",
    "in.outros_recebimentos.donativos": "Donations Received",
    "in.outros_recebimentos.herancas": "Inheritance",
    "in.outros_recebimentos.outros": "Other",

    // Habitação
    "out.habitacao.prestacao": "Mortgage Payment",
    "out.habitacao.renda": "Rent",
    "out.habitacao.agua_eletricidade_e_gas": "Water, Electricity & Gas",
    "out.habitacao.telecomunicacoes": "Telecommunications",
    "out.habitacao.bens_mobiliarios": "Furniture & Household Goods",
    "out.habitacao.seguranca": "Security",
    "out.habitacao.condominio": "Condo Fees",
    "out.habitacao.servicos_domesticos": "Household Services",
    "out.habitacao.outros": "Other",
    // Alimentação
    "out.alimentacao.supermercado": "Supermarket",
    "out.alimentacao.restaurantes_e_cafes": "Restaurants & Cafés",
    "out.alimentacao.outros": "Other",
    // Transportes
    "out.transportes.prestacao": "Car Loan Payment",
    "out.transportes.combustivel": "Fuel",
    "out.transportes.manutencao_e_inspecao": "Maintenance & Inspection",
    "out.transportes.portagens_e_estacionamento": "Tolls & Parking",
    "out.transportes.transportes_publicos_e_tvde": "Public Transport & Rideshare",
    "out.transportes.outros": "Other",
    // Educação
    "out.educacao.cursos_e_formacoes": "Courses & Training",
    "out.educacao.livros_e_material": "Books & Materials",
    "out.educacao.outros": "Other",
    // Saúde e Auto-Cuidado
    "out.saude_e_auto_cuidado.consultas_e_exames": "Consultations & Exams",
    "out.saude_e_auto_cuidado.tratamentos_e_medicamentos": "Treatments & Medication",
    "out.saude_e_auto_cuidado.servicos_de_bem_estar": "Wellness Services",
    "out.saude_e_auto_cuidado.outros": "Other",
    // Entretenimento
    "out.entretenimento.viagens": "Travel",
    "out.entretenimento.eventos": "Events",
    "out.entretenimento.subscricoes": "Subscriptions",
    "out.entretenimento.outros": "Other",
    // Tecnologia
    "out.tecnologia.hardware": "Hardware",
    "out.tecnologia.software": "Software",
    "out.tecnologia.outros": "Other",
    // Impostos
    "out.impostos.irs": "Income Tax (IRS)",
    "out.impostos.iuc": "Vehicle Tax (IUC)",
    "out.impostos.imi": "Property Tax (IMI)",
    "out.impostos.coimas": "Fines",
    "out.impostos.outros": "Other",
    // Seguros
    "out.seguros.habitacao": "Home",
    "out.seguros.automovel": "Car",
    "out.seguros.saude": "Health",
    "out.seguros.vida": "Life",
    "out.seguros.outros": "Other",
    // Serviços Financeiros
    "out.servicos_financeiros.juros": "Interest",
    "out.servicos_financeiros.comissoes": "Fees",
    "out.servicos_financeiros.outros": "Other",
    // Compra de Ativos (para Investimento)
    "out.compra_de_ativos_para_investimento.imoveis": "Real Estate",
    "out.compra_de_ativos_para_investimento.veiculos": "Vehicles",
    "out.compra_de_ativos_para_investimento.equipamentos": "Equipment",
    "out.compra_de_ativos_para_investimento.ativos_financeiros": "Financial Assets",
    "out.compra_de_ativos_para_investimento.outros": "Other",
    // Transferências Próprias (saídas)
    "out.transferencias_proprias.entre_contas": "Between Accounts",
    "out.transferencias_proprias.levantamento_em_numerario": "Cash Withdrawal",
    "out.transferencias_proprias.outros": "Other",
    // Outros Pagamentos
    "out.outros_pagamentos.presentes": "Gifts",
    "out.outros_pagamentos.donativos": "Donations Made",
    "out.outros_pagamentos.quotas": "Membership Fees",
    "out.outros_pagamentos.outros": "Other",
  },
}

// mensagens de erro do backend (code -> texto) — só entram aqui quando o code já foi
// traduzido; sem entrada, mensagemDeErro() cai sempre no "message" (em português) que o
// backend já devolve, nunca mostra uma chave em bruto.
export const ERROS_TRADUCOES = {
  en: {
    // validação genérica (Pydantic — ver core/errors.py)
    MISSING: () => "This field is required.",
    STRING_TOO_SHORT: (ctx) => `Must be at least ${ctx.min_length} characters.`,
    STRING_TOO_LONG: (ctx) => `Cannot be more than ${ctx.max_length} characters.`,
    STRING_TYPE: () => "Must be text.",
    INT_TYPE: () => "Must be a whole number.",
    INT_PARSING: () => "Must be a valid whole number.",
    FLOAT_TYPE: () => "Must be a number.",
    FLOAT_PARSING: () => "Must be a valid number.",
    BOOL_TYPE: () => "Must be true or false.",
    BOOL_PARSING: () => "Invalid value — expected true or false.",
    DATE_TYPE: () => "Must be a valid date.",
    DATE_FROM_DATETIME_PARSING: () => "Must be a valid date (YYYY-MM-DD).",
    DATE_FROM_DATETIME_INEXACT: () => "Must be a date, without a time.",
    VALUE_ERROR: () => "Invalid email.",   // hoje o único uso de "value_error" nesta app

    // autenticação
    EMAIL_JA_REGISTADO: () => "Email already registered",
    CREDENCIAIS_INVALIDAS: () => "Incorrect email or password",
    TOKEN_INVALIDO: () => "Invalid or expired token",
    SESSAO_TERMINADA: () => "Session ended. Please log in again.",
    TOKEN_JA_UTILIZADO: () => "Invalid or already used link",
    PASSWORD_INCORRETA: () => "Current password is incorrect",
    EMAIL_EM_USO: () => "Email already in use",

    // contas / reconciliações
    CONTA_NAO_ENCONTRADA: () => "Account not found",
    DATA_FUTURA: () => "Cannot use a future date",
    CONTA_COM_MOVIMENTOS: (ctx) => `This account has ${ctx.n ?? ""} associated transaction(s). Deleting the account will also delete them.`,
    INICIO_NO_FUTURO: () => "Cannot set a start date in the future.",
    INICIO_APOS_PRIMEIRO_MOVIMENTO: () => "Cannot set the transaction start date after a transaction you already have recorded.",
    INICIO_ULTRAPASSA_RECONCILIACOES: () => "This start date is past existing reconciliations. Confirm to delete them.",
    RECONCILIACAO_ANTES_DO_INICIO: () => "Cannot set a reconciliation before this account's transaction start date.",
    RECONCILIACAO_DUPLICADA: () => "Cannot have two reconciliations on the same date.",
    RECONCILIACAO_NAO_ENCONTRADA: () => "Reconciliation not found",
    SEM_RECONCILIACAO_ANTERIOR: () => "There's no reconciliation before this date.",

    // categorias / grupos
    CATEGORIA_NAO_ENCONTRADA: () => "Category not found",
    CATEGORIA_PROTEGIDA: () => "This category is required for the system to work and cannot be changed or deleted.",
    CATEGORIA_COM_MOVIMENTOS: (ctx) => `${ctx.n ?? ""} transaction(s) use this category.`,
    CATEGORIA_DESTINO_NAO_ENCONTRADA: () => "Destination category not found",
    CATEGORIA_DIRECAO_ERRADA: (ctx) => `Cannot save this transaction: it needs a category of type ${ctx.eh_recebimento ? "Income" : "Expense"}.`,
    GRUPO_NAO_ENCONTRADO: () => "Group not found",
    GRUPO_DESTINO_NAO_ENCONTRADO: () => "Destination group not found",
    GRUPO_NAO_PODE_SER_SUBCATEGORIA: () => "A group cannot be moved inside another group.",
    GRUPO_COM_CATEGORIAS: (ctx) => `This group has ${ctx.n ?? ""} categor${ctx.n === 1 ? "y" : "ies"}. Choose a destination group or confirm full deletion.`,
    GRUPO_TEM_CATEGORIA_PROTEGIDA: () => "This group contains a category required by the system and cannot be deleted.",
    DIRECAO_EM_FALTA: () => "A new group needs to specify whether it's Income or Expense.",
    DESTINO_TIPO_INCOMPATIVEL: () => "The destination must be of the same type (group or category).",
    DESTINO_DIRECAO_INCOMPATIVEL: () => "The destination must be of the same direction (Income or Expense).",

    // movimentos / stats
    MOVIMENTO_NAO_ENCONTRADO: () => "Transaction not found",
    MOVIMENTO_ANTES_DO_INICIO: (ctx) => {
      const [ano, mes, dia] = (ctx.data || "").split("-")
      const data = dia && mes && ano ? `${dia}-${mes}-${ano}` : ""
      return `Cannot record a transaction before ${data}, this account's transaction start date.`
    },
    EXCLUIR_CATEGORIAS_INVALIDO: () => "excluir_categorias must be a comma-separated list of ids.",
    PARAMETRO_EM_FALTA: () => "Specify grupo_id or categoria_id.",
    PARAMETROS_EXCLUSIVOS: () => "Specify only grupo_id or only categoria_id, not both.",
  },
}

/** Traduz uma string simples, com fallback pt -> a própria chave (nunca mostra "undefined"). */
export function t(chave) {
  return TRADUCOES[estadoGlobal.lingua]?.[chave] ?? TRADUCOES.pt[chave] ?? chave
}

/** Traduz o nome de uma categoria/grupo pelo seu slug estável (ver migração
 * 0014_slug_categorias.sql). `slug` vem null nas categorias criadas pelo próprio
 * utilizador: devolve sempre `nome` tal como está, nas duas línguas — não há "original"
 * para comparar, por isso nunca há tradução automática para estas.
 *
 * Nas categorias por omissão (slug preenchido), só traduz enquanto `nome` continuar
 * igual ao nome de fábrica (`CATEGORIAS_TRADUCOES.pt[slug]`). Assim que o utilizador a
 * renomeia — para o que for, "Compras da Semana" ou qualquer outra coisa sem relação
 * nenhuma com a categoria original — deixa de fazer sentido continuar a mostrar a
 * tradução antiga ("Supermarket") ignorando o texto novo; a partir daí mostra-se sempre
 * o nome tal como o utilizador o escreveu, nas duas línguas, como uma categoria seria
 * tratada se fosse toda dele. Reversível: se voltar a escrever exactamente o nome de
 * fábrica, a tradução automática retoma sozinha. */
export function nomeCategoria(nome, slug) {
  if (!slug) return nome
  const nomeDeFabrica = CATEGORIAS_TRADUCOES.pt[slug]
  if (nomeDeFabrica && nome !== nomeDeFabrica) return nome
  if (estadoGlobal.lingua === "pt") return nome
  return CATEGORIAS_TRADUCOES.en[slug] ?? nome
}

// Nomes de meses/dias da semana — usados nos gráficos (Chart.js) e no calendário próprio
// (ver static/js/calendario.js); tabela por língua em vez de chaves t() avulsas porque o
// formato (array com 12/7 posições fixas) é o que os chamadores precisam directamente.
const MESES_ABREV      = { pt: ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"], en: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"] }
const MESES_COMPLETOS  = { pt: ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"], en: ["January","February","March","April","May","June","July","August","September","October","November","December"] }
const DIAS_SEMANA_ABREV = { pt: ["S","T","Q","Q","S","S","D"], en: ["M","T","W","T","F","S","S"] }

export function nomesMesesAbrev()     { return MESES_ABREV[estadoGlobal.lingua] ?? MESES_ABREV.pt }
export function nomesMesesCompletos() { return MESES_COMPLETOS[estadoGlobal.lingua] ?? MESES_COMPLETOS.pt }
export function nomesDiasAbrev()      { return DIAS_SEMANA_ABREV[estadoGlobal.lingua] ?? DIAS_SEMANA_ABREV.pt }

/** Traduz {code, message, ctx} do backend — cai sempre no message (PT) do backend se o
 * código ainda não tiver entrada na língua actual (ex. páginas por migrar). */
export function traduzirErro(detalhe) {
  const fn = ERROS_TRADUCOES[estadoGlobal.lingua]?.[detalhe.code]
  if (!fn) return detalhe.message
  try {
    return fn(detalhe.ctx || {})
  } catch {
    return detalhe.message
  }
}

/** Varre o DOM à procura de data-i18n(-placeholder|-aria-label|-ajuda) e aplica a tradução
 * actual — chamado uma vez no arranque e sempre que a língua muda. */
export function aplicarTraducoes(raiz = document) {
  raiz.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n) })
  raiz.querySelectorAll("[data-i18n-placeholder]").forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder) })
  raiz.querySelectorAll("[data-i18n-aria-label]").forEach(el => { el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel)) })
  raiz.querySelectorAll("[data-i18n-ajuda]").forEach(el => { el.dataset.ajuda = t(el.dataset.i18nAjuda) })

  document.querySelectorAll("#toggle-lingua button").forEach(b => b.classList.remove("active"))
  document.getElementById("lingua-" + estadoGlobal.lingua)?.classList.add("active")
}
