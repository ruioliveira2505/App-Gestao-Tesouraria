-- Slug estável para categorias de sistema (semeadas por omissão no registo, ver
-- app/services/categorias_seed.py), para o i18n do frontend traduzir o NOME de uma
-- categoria sem depender do texto actual — ao contrário do nome, o slug nunca muda depois
-- de atribuído, mesmo que o utilizador renomeie a categoria. NULL para categorias criadas
-- pelo próprio utilizador (não faz sentido traduzir texto que a pessoa escreveu).
-- Formato: "<in|out>.<grupo>[.<categoria>]" — a direcção entra no slug porque
-- "Transferências Próprias" existe como grupo tanto em entradas como em saídas.
ALTER TABLE categorias ADD COLUMN slug text;

CREATE UNIQUE INDEX categorias_utilizador_slug_unico
    ON categorias (utilizador_id, slug) WHERE slug IS NOT NULL;

-- Backfill: atribui o slug às categorias de sistema já existentes, casando por nome —
-- válido só neste momento único (assume que ainda não foram renomeadas); a partir daqui o
-- slug deixa de ter qualquer ligação ao nome. Gerado a partir de ARVORE_PADRAO
-- (categorias_seed.py) por um script à parte, para não transcrever ~100 slugs à mão.

-- grupos
UPDATE categorias SET slug = 'in.trabalho' WHERE nome = 'Trabalho' AND eh_recebimento = true AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'in.investimentos' WHERE nome = 'Investimentos' AND eh_recebimento = true AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'in.venda_de_ativos' WHERE nome = 'Venda de Ativos' AND eh_recebimento = true AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'in.emprestimos' WHERE nome = 'Empréstimos' AND eh_recebimento = true AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'in.transferencias_proprias' WHERE nome = 'Transferências Próprias' AND eh_recebimento = true AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'in.outros_recebimentos' WHERE nome = 'Outros Recebimentos' AND eh_recebimento = true AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao' WHERE nome = 'Habitação' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.alimentacao' WHERE nome = 'Alimentação' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.transportes' WHERE nome = 'Transportes' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.educacao' WHERE nome = 'Educação' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.saude_e_auto_cuidado' WHERE nome = 'Saúde e Auto-Cuidado' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.entretenimento' WHERE nome = 'Entretenimento' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.tecnologia' WHERE nome = 'Tecnologia' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.impostos' WHERE nome = 'Impostos' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.seguros' WHERE nome = 'Seguros' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.servicos_financeiros' WHERE nome = 'Serviços Financeiros' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.compra_de_ativos_para_investimento' WHERE nome = 'Compra de Ativos (para Investimento)' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.transferencias_proprias' WHERE nome = 'Transferências Próprias' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;
UPDATE categorias SET slug = 'out.outros_pagamentos' WHERE nome = 'Outros Pagamentos' AND eh_recebimento = false AND parent_id IS NULL AND slug IS NULL;

-- categorias-folha (por nome do grupo pai, já com slug atribuído acima)
UPDATE categorias SET slug = 'in.trabalho.salario' WHERE nome = 'Salário' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.trabalho') AND slug IS NULL;
UPDATE categorias SET slug = 'in.trabalho.premios' WHERE nome = 'Prémios' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.trabalho') AND slug IS NULL;
UPDATE categorias SET slug = 'in.trabalho.recibos_verdes' WHERE nome = 'Recibos Verdes' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.trabalho') AND slug IS NULL;
UPDATE categorias SET slug = 'in.trabalho.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.trabalho') AND slug IS NULL;
UPDATE categorias SET slug = 'in.investimentos.renda_de_imoveis' WHERE nome = 'Renda de Imóveis' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.investimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.investimentos.dividendos' WHERE nome = 'Dividendos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.investimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.investimentos.juros' WHERE nome = 'Juros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.investimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.investimentos.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.investimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.venda_de_ativos.imoveis' WHERE nome = 'Imóveis' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.venda_de_ativos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.venda_de_ativos.veiculos' WHERE nome = 'Veículos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.venda_de_ativos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.venda_de_ativos.equipamentos' WHERE nome = 'Equipamentos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.venda_de_ativos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.venda_de_ativos.ativos_financeiros' WHERE nome = 'Ativos Financeiros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.venda_de_ativos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.venda_de_ativos.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.venda_de_ativos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.emprestimos.credito_pessoal' WHERE nome = 'Crédito Pessoal' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.emprestimos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.emprestimos.emprestimo_particular' WHERE nome = 'Empréstimo Particular' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.emprestimos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.emprestimos.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.emprestimos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.transferencias_proprias.entre_contas' WHERE nome = 'Entre Contas' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.transferencias_proprias') AND slug IS NULL;
UPDATE categorias SET slug = 'in.transferencias_proprias.deposito_em_numerario' WHERE nome = 'Depósito em Numerário' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.transferencias_proprias') AND slug IS NULL;
UPDATE categorias SET slug = 'in.transferencias_proprias.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.transferencias_proprias') AND slug IS NULL;
UPDATE categorias SET slug = 'in.outros_recebimentos.reembolsos' WHERE nome = 'Reembolsos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.outros_recebimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.outros_recebimentos.presentes' WHERE nome = 'Presentes' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.outros_recebimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.outros_recebimentos.donativos' WHERE nome = 'Donativos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.outros_recebimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.outros_recebimentos.herancas' WHERE nome = 'Heranças' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.outros_recebimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'in.outros_recebimentos.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'in.outros_recebimentos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.prestacao' WHERE nome = 'Prestação' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.renda' WHERE nome = 'Renda' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.agua_eletricidade_e_gas' WHERE nome = 'Água, Eletricidade e Gás' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.telecomunicacoes' WHERE nome = 'Telecomunicações' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.bens_mobiliarios' WHERE nome = 'Bens Mobiliários' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.seguranca' WHERE nome = 'Segurança' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.condominio' WHERE nome = 'Condomínio' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.servicos_domesticos' WHERE nome = 'Serviços Domésticos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.habitacao.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.habitacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.alimentacao.supermercado' WHERE nome = 'Supermercado' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.alimentacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.alimentacao.restaurantes_e_cafes' WHERE nome = 'Restaurantes e Cafés' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.alimentacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.alimentacao.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.alimentacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transportes.prestacao' WHERE nome = 'Prestação' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transportes') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transportes.combustivel' WHERE nome = 'Combustível' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transportes') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transportes.manutencao_e_inspecao' WHERE nome = 'Manutenção e Inspeção' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transportes') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transportes.portagens_e_estacionamento' WHERE nome = 'Portagens e Estacionamento' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transportes') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transportes.transportes_publicos_e_tvde' WHERE nome = 'Transportes Públicos e TVDE' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transportes') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transportes.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transportes') AND slug IS NULL;
UPDATE categorias SET slug = 'out.educacao.cursos_e_formacoes' WHERE nome = 'Cursos e Formações' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.educacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.educacao.livros_e_material' WHERE nome = 'Livros e Material' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.educacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.educacao.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.educacao') AND slug IS NULL;
UPDATE categorias SET slug = 'out.saude_e_auto_cuidado.consultas_e_exames' WHERE nome = 'Consultas e Exames' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.saude_e_auto_cuidado') AND slug IS NULL;
UPDATE categorias SET slug = 'out.saude_e_auto_cuidado.tratamentos_e_medicamentos' WHERE nome = 'Tratamentos e Medicamentos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.saude_e_auto_cuidado') AND slug IS NULL;
UPDATE categorias SET slug = 'out.saude_e_auto_cuidado.servicos_de_bem_estar' WHERE nome = 'Serviços de Bem-Estar' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.saude_e_auto_cuidado') AND slug IS NULL;
UPDATE categorias SET slug = 'out.saude_e_auto_cuidado.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.saude_e_auto_cuidado') AND slug IS NULL;
UPDATE categorias SET slug = 'out.entretenimento.viagens' WHERE nome = 'Viagens' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.entretenimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.entretenimento.eventos' WHERE nome = 'Eventos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.entretenimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.entretenimento.subscricoes' WHERE nome = 'Subscrições' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.entretenimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.entretenimento.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.entretenimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.tecnologia.hardware' WHERE nome = 'Hardware' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.tecnologia') AND slug IS NULL;
UPDATE categorias SET slug = 'out.tecnologia.software' WHERE nome = 'Software' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.tecnologia') AND slug IS NULL;
UPDATE categorias SET slug = 'out.tecnologia.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.tecnologia') AND slug IS NULL;
UPDATE categorias SET slug = 'out.impostos.irs' WHERE nome = 'IRS' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.impostos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.impostos.iuc' WHERE nome = 'IUC' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.impostos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.impostos.imi' WHERE nome = 'IMI' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.impostos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.impostos.coimas' WHERE nome = 'Coimas' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.impostos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.impostos.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.impostos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.seguros.habitacao' WHERE nome = 'Habitação' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.seguros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.seguros.automovel' WHERE nome = 'Automóvel' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.seguros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.seguros.saude' WHERE nome = 'Saúde' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.seguros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.seguros.vida' WHERE nome = 'Vida' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.seguros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.seguros.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.seguros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.servicos_financeiros.juros' WHERE nome = 'Juros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.servicos_financeiros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.servicos_financeiros.comissoes' WHERE nome = 'Comissões' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.servicos_financeiros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.servicos_financeiros.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.servicos_financeiros') AND slug IS NULL;
UPDATE categorias SET slug = 'out.compra_de_ativos_para_investimento.imoveis' WHERE nome = 'Imóveis' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.compra_de_ativos_para_investimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.compra_de_ativos_para_investimento.veiculos' WHERE nome = 'Veículos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.compra_de_ativos_para_investimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.compra_de_ativos_para_investimento.equipamentos' WHERE nome = 'Equipamentos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.compra_de_ativos_para_investimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.compra_de_ativos_para_investimento.ativos_financeiros' WHERE nome = 'Ativos Financeiros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.compra_de_ativos_para_investimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.compra_de_ativos_para_investimento.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.compra_de_ativos_para_investimento') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transferencias_proprias.entre_contas' WHERE nome = 'Entre Contas' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transferencias_proprias') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transferencias_proprias.levantamento_em_numerario' WHERE nome = 'Levantamento em Numerário' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transferencias_proprias') AND slug IS NULL;
UPDATE categorias SET slug = 'out.transferencias_proprias.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.transferencias_proprias') AND slug IS NULL;
UPDATE categorias SET slug = 'out.outros_pagamentos.presentes' WHERE nome = 'Presentes' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.outros_pagamentos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.outros_pagamentos.donativos' WHERE nome = 'Donativos' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.outros_pagamentos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.outros_pagamentos.quotas' WHERE nome = 'Quotas' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.outros_pagamentos') AND slug IS NULL;
UPDATE categorias SET slug = 'out.outros_pagamentos.outros' WHERE nome = 'Outros' AND parent_id IN (SELECT id FROM categorias WHERE slug = 'out.outros_pagamentos') AND slug IS NULL;
