"""Árvore de categorias por omissão, semeada para cada utilizador novo (ver
services/auth.py::criar_utilizador) — dados fixos, sem regra de negócio nenhuma."""

import re
import unicodedata

from psycopg2.extras import RealDictCursor, execute_values

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


def _slugificar(texto: str) -> str:
    """"Água, Eletricidade e Gás" -> "agua_eletricidade_e_gas" — usado para o slug estável
    de tradução (ver migração 0014_slug_categorias.sql); nunca para nada visível ao
    utilizador."""
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", sem_acentos.lower()).strip("_")


def _slug_grupo(nome_grupo: str, eh_recebimento: bool) -> str:
    # a direcção entra no slug porque "Transferências Próprias" existe como grupo tanto em
    # entradas como em saídas — sem isto os dois colidiam no mesmo slug.
    return f"{'in' if eh_recebimento else 'out'}.{_slugificar(nome_grupo)}"


def seed_categorias_padrao(cursor: RealDictCursor, utilizador_id: int) -> None:
    """Não comita — fica na mesma transacção de quem chamar (ver criar_utilizador em
    services/auth.py: se o seed falhar a meio, a conta criada mesmo antes tem de cair
    também, não pode ficar uma conta órfã com o email já ocupado).

    Dois INSERTs em bloco (grupos, depois categorias-folha) em vez de ~98 INSERTs
    individuais — os grupos têm de vir primeiro porque as folhas precisam do id do grupo
    já atribuído pela BD. A correspondência entre os grupos inseridos e os ids devolvidos
    por RETURNING depende da ordem de inserção ser preservada (garantido para um único
    INSERT ... VALUES multi-linha, sem ON CONFLICT — é o mesmo pressuposto que qualquer
    bulk-insert com RETURNING faz); `test_arvore_tem_todos_os_grupos_com_subcategorias_corretas`
    verifica isto explicitamente, não só de raspão."""
    grupos_valores = [
        (nome_grupo, eh_recebimento, ordem_grupo, utilizador_id, _slug_grupo(nome_grupo, eh_recebimento))
        for ordem_grupo, (nome_grupo, eh_recebimento, _) in enumerate(ARVORE_PADRAO, start=1)
    ]
    grupo_ids = execute_values(
        cursor,
        "INSERT INTO categorias (nome, eh_recebimento, ordem, utilizador_id, slug) VALUES %s RETURNING id",
        grupos_valores,
        fetch=True,
    )

    categorias_valores = []
    for (nome_grupo, eh_recebimento, categorias), grupo_id_row in zip(ARVORE_PADRAO, grupo_ids, strict=True):
        grupo_id = grupo_id_row["id"]
        slug_grupo = _slug_grupo(nome_grupo, eh_recebimento)
        for ordem_cat, nome_cat in enumerate(categorias, start=1):
            protegida = nome_grupo in GRUPOS_COM_OUTROS_PROTEGIDO and nome_cat == "Outros"
            slug = f"{slug_grupo}.{_slugificar(nome_cat)}"
            categorias_valores.append((nome_cat, grupo_id, eh_recebimento, ordem_cat, utilizador_id, protegida, slug))

    execute_values(
        cursor,
        "INSERT INTO categorias (nome, parent_id, eh_recebimento, ordem, utilizador_id, protegida, slug) VALUES %s",
        categorias_valores,
    )