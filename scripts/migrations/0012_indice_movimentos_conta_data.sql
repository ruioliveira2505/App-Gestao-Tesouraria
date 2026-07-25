-- movimentos já tinha índices separados em conta_id e em data, mas várias queries filtram
-- pelos dois ao mesmo tempo (ex. GET /stats/saldo-diario, que faz uma subquery por
-- dia × conta a somar movimentos "WHERE conta_id = ... AND data > ... AND data <= ...") —
-- um índice composto serve isso directamente, em vez de o Postgres ter de combinar dois
-- índices separados (BitmapAnd) a cada chamada.
CREATE INDEX idx_movimentos_conta_data ON movimentos (conta_id, data);
