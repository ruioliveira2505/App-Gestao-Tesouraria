ARVORE_PADRAO = [
    ("Trabalho", True, ["Salário", "Prémios", "Recibos Verdes", "Outros"]),
    ("Investimentos", True, ["Renda de Imóveis", "Dividendos", "Juros", "Outros"]),
    ("Venda de Ativos", True, ["Imóveis", "Veículos", "Equipamentos", "Ativos Financeiros", "Outros"]),
    ("Empréstimos", True, ["Crédito Pessoal", "Empréstimo Particular", "Outros"]),
    ("Transferências Próprias", True, ["Entre Contas", "Depósito em Numerário", "Outros"]),
    ("Outros Recebimentos", True, ["Reembolsos", "Presentes", "Donativos", "Heranças", "Outros"]),

    ("Habitação", False, ["Prestação", "Renda", "Água, Eletricidade e Gás", "Telecomunicações", "Bens Mobiliários", "Segurança", "Condomínio", "Serviços Domésticos", "Outros"]),
    ("Alimentação", False, ["Supermercado", "Restaurantes e Cafés", "Outros"]),
    ("Transportes", False, ["Prestação", "Combustível", "Manutenção e Inspeção", "Portagens e Estacionamento", "Transportes Públicos e TVDE", "Outros"]),
    ("Educação", False, ["Cursos e Formações", "Livros e Material", "Outros"]),
    ("Saúde e Auto-Cuidado", False, ["Consultas e Exames", "Tratamentos e Medicamentos", "Serviços de Bem-Estar", "Outros"]),
    ("Entretenimento", False, ["Viagens", "Eventos", "Subscrições", "Outros"]),
    ("Tecnologia", False, ["Hardware", "Software", "Outros"]),
    ("Impostos", False, ["IRS", "IUC", "IMI", "Coimas", "Outros"]),
    ("Seguros", False, ["Habitação", "Automóvel", "Saúde", "Vida", "Outros"]),
    ("Serviços Financeiros", False, ["Juros", "Comissões", "Outros"]),
    ("Compra de Ativos (para Investimento)", False, ["Imóveis", "Veículos", "Equipamentos", "Ativos Financeiros", "Outros"]),
    ("Transferências Próprias", False, ["Entre Contas", "Levantamento em Numerário", "Outros"]),
    ("Outros Pagamentos", False, ["Presentes", "Donativos", "Quotas", "Outros"]),
]

# Dentro destes dois grupos, a categoria-folha "Outros" é o destino estrutural
# do fallback do sistema — fica protegida (nunca pode ser renomeada ou
# eliminada). Os grupos à volta, e as outras subcategorias, ficam livres.
GRUPOS_COM_OUTROS_PROTEGIDO = {"Outros Recebimentos", "Outros Pagamentos"}


def seed_categorias_padrao(conn, utilizador_id):
    cursor = conn.cursor()

    for ordem_grupo, (nome_grupo, eh_recebimento, categorias) in enumerate(ARVORE_PADRAO, start=1):
        cursor.execute("""
            INSERT INTO categorias (nome, eh_recebimento, ordem, utilizador_id)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (nome_grupo, eh_recebimento, ordem_grupo, utilizador_id))
        grupo_id = cursor.fetchone()[0]

        for ordem_cat, nome_cat in enumerate(categorias, start=1):
            protegida = nome_grupo in GRUPOS_COM_OUTROS_PROTEGIDO and nome_cat == "Outros"
            cursor.execute("""
                INSERT INTO categorias (nome, parent_id, eh_recebimento, ordem, utilizador_id, protegida)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nome_cat, grupo_id, eh_recebimento, ordem_cat, utilizador_id, protegida))

    conn.commit()
    cursor.close()