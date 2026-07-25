-- A âncora (saldo inicial + data) deixa de ser uma linha "escondida" dentro de
-- ajustes_saldo (identificada só por ser a mais antiga, uma convenção implícita) e passa a
-- ser um atributo próprio de contas — ajustes_saldo fica só com reconciliações reais.
-- contas.saldo (nunca lido por nenhuma query, só escrito) sai também, por já não servir
-- para nada.

ALTER TABLE contas
    ADD COLUMN data_ancora date,
    ADD COLUMN saldo_ancora numeric(12,2);

-- backfill: para cada conta, a linha mais antiga de ajustes_saldo É a âncora (garantido
-- pelas validações da aplicação — nenhuma reconciliação real pode ser mais antiga que ela).
UPDATE contas c
SET data_ancora = a.data, saldo_ancora = a.saldo_real
FROM (
    SELECT DISTINCT ON (conta_id) conta_id, data, saldo_real
    FROM ajustes_saldo
    ORDER BY conta_id, data ASC
) a
WHERE a.conta_id = c.id;

ALTER TABLE contas
    ALTER COLUMN data_ancora SET NOT NULL,
    ALTER COLUMN saldo_ancora SET NOT NULL;

-- remove de ajustes_saldo a linha que acabou de ser copiada para contas — a partir daqui
-- a tabela só tem reconciliações reais.
DELETE FROM ajustes_saldo a
USING (
    SELECT DISTINCT ON (conta_id) id
    FROM ajustes_saldo
    ORDER BY conta_id, data ASC
) mais_antiga
WHERE a.id = mais_antiga.id;

ALTER TABLE contas DROP COLUMN saldo;
