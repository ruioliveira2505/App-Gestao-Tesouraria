-- Email deixa de ser sensível a maiúsculas/minúsculas: "User@x.com" e "user@x.com" passam
-- a contar como o mesmo email, tanto para o UNIQUE constraint como para comparações em
-- WHERE. citext preserva a capitalização como foi escrita (mostra "User@x.com" de volta),
-- só a comparação/ordenação é que ignora maiúsculas — não precisa de mudar nenhuma query
-- Python (WHERE email = %s continua a funcionar, agora de forma insensível a maiúsculas).
CREATE EXTENSION IF NOT EXISTS citext;

ALTER TABLE utilizadores ALTER COLUMN email TYPE citext;
