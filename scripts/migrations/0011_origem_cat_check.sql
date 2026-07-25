-- movimentos.origem_cat era texto livre — nada impedia gravar um valor fora dos 4 que o
-- código sabe interpretar ("manual" | "cache" | "llm" | "sem_match", ver
-- services/categorizacao.py). Um valor fora disto não dava erro nenhum ao gravar, só
-- fazia o movimento aparecer com um "confirmado"/"sem_categoria" incoerente na resposta
-- da API (services/movimentos.py::listar_movimentos calcula isso a partir do valor).
ALTER TABLE movimentos ADD CONSTRAINT movimentos_origem_cat_check
    CHECK (origem_cat IN ('manual', 'cache', 'llm', 'sem_match'));
