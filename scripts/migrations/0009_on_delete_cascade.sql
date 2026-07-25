-- Substitui a cascata de eliminação manual (feita em Python) por ON DELETE CASCADE nas
-- FKs relevantes — a base de dados passa a garantir a integridade referencial, em vez de
-- depender de cada endpoint se lembrar de limpar tudo pela ordem certa. Isto é também o
-- que teria evitado o bug de categorias_aprendidas corrigido anteriormente em
-- _eliminar_folha, caso alguém se esquecesse de novo no futuro.

ALTER TABLE categorias_aprendidas DROP CONSTRAINT categorias_aprendidas_categoria_id_fkey;
ALTER TABLE categorias_aprendidas ADD CONSTRAINT categorias_aprendidas_categoria_id_fkey
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE;

ALTER TABLE categorias_aprendidas DROP CONSTRAINT categorias_aprendidas_utilizador_id_fkey;
ALTER TABLE categorias_aprendidas ADD CONSTRAINT categorias_aprendidas_utilizador_id_fkey
    FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id) ON DELETE CASCADE;

ALTER TABLE categorias DROP CONSTRAINT categorias_parent_id_fkey;
ALTER TABLE categorias ADD CONSTRAINT categorias_parent_id_fkey
    FOREIGN KEY (parent_id) REFERENCES categorias(id) ON DELETE CASCADE;

ALTER TABLE categorias DROP CONSTRAINT categorias_utilizador_id_fkey;
ALTER TABLE categorias ADD CONSTRAINT categorias_utilizador_id_fkey
    FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id) ON DELETE CASCADE;

ALTER TABLE contas DROP CONSTRAINT contas_utilizador_id_fkey;
ALTER TABLE contas ADD CONSTRAINT contas_utilizador_id_fkey
    FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id) ON DELETE CASCADE;

ALTER TABLE movimentos DROP CONSTRAINT movimentos_categoria_id_fkey;
ALTER TABLE movimentos ADD CONSTRAINT movimentos_categoria_id_fkey
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE;

ALTER TABLE movimentos DROP CONSTRAINT movimentos_conta_id_fkey;
ALTER TABLE movimentos ADD CONSTRAINT movimentos_conta_id_fkey
    FOREIGN KEY (conta_id) REFERENCES contas(id) ON DELETE CASCADE;

ALTER TABLE movimentos DROP CONSTRAINT movimentos_utilizador_id_fkey;
ALTER TABLE movimentos ADD CONSTRAINT movimentos_utilizador_id_fkey
    FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id) ON DELETE CASCADE;
