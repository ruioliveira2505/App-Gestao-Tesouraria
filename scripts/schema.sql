--
-- PostgreSQL database dump
--

\restrict 5iQJRYQpXZxlHMZ6CNpoCafRhdrWRAXbwaQZkTaPUHQTuDA6amDrGe3WuOIlOPS

-- Dumped from database version 18.4 (Ubuntu 18.4-0ubuntu0.26.04.1)
-- Dumped by pg_dump version 18.4 (Ubuntu 18.4-0ubuntu0.26.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ajustes_saldo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ajustes_saldo (
    id integer NOT NULL,
    conta_id text,
    data date NOT NULL,
    saldo_real numeric NOT NULL,
    criado_em timestamp without time zone DEFAULT now()
);


ALTER TABLE public.ajustes_saldo OWNER TO postgres;

--
-- Name: ajustes_saldo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ajustes_saldo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ajustes_saldo_id_seq OWNER TO postgres;

--
-- Name: ajustes_saldo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ajustes_saldo_id_seq OWNED BY public.ajustes_saldo.id;


--
-- Name: categorias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias (
    id integer NOT NULL,
    nome text NOT NULL,
    parent_id integer,
    eh_recebimento boolean,
    utilizador_id integer NOT NULL,
    criado_em timestamp without time zone DEFAULT now(),
    ordem integer DEFAULT 0,
    protegida boolean DEFAULT false NOT NULL
);


ALTER TABLE public.categorias OWNER TO postgres;

--
-- Name: categorias_aprendidas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias_aprendidas (
    id integer NOT NULL,
    descricao text NOT NULL,
    categoria_id integer NOT NULL,
    utilizador_id integer NOT NULL,
    criado_em timestamp without time zone DEFAULT now(),
    confirmado boolean DEFAULT false NOT NULL
);


ALTER TABLE public.categorias_aprendidas OWNER TO postgres;

--
-- Name: categorias_aprendidas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.categorias_aprendidas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_aprendidas_id_seq OWNER TO postgres;

--
-- Name: categorias_aprendidas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.categorias_aprendidas_id_seq OWNED BY public.categorias_aprendidas.id;


--
-- Name: categorias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_id_seq OWNER TO postgres;

--
-- Name: categorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;


--
-- Name: contas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contas (
    id text NOT NULL,
    banco text NOT NULL,
    iban text NOT NULL,
    moeda text DEFAULT 'EUR'::text NOT NULL,
    saldo numeric(12,2) DEFAULT 0 NOT NULL,
    criado_em timestamp without time zone DEFAULT now(),
    utilizador_id integer,
    tipo text DEFAULT 'corrente'::text NOT NULL,
    nome text NOT NULL
);


ALTER TABLE public.contas OWNER TO postgres;

--
-- Name: movimentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movimentos (
    id text NOT NULL,
    conta_id text NOT NULL,
    data date NOT NULL,
    descricao text NOT NULL,
    valor numeric(12,2) NOT NULL,
    origem_cat text,
    criado_em timestamp without time zone DEFAULT now(),
    utilizador_id integer,
    categoria_id integer NOT NULL
);


ALTER TABLE public.movimentos OWNER TO postgres;

--
-- Name: utilizadores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.utilizadores (
    id integer NOT NULL,
    nome text NOT NULL,
    email text NOT NULL,
    password text NOT NULL,
    criado_em timestamp without time zone DEFAULT now()
);


ALTER TABLE public.utilizadores OWNER TO postgres;

--
-- Name: utilizadores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.utilizadores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.utilizadores_id_seq OWNER TO postgres;

--
-- Name: utilizadores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.utilizadores_id_seq OWNED BY public.utilizadores.id;


--
-- Name: ajustes_saldo id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ajustes_saldo ALTER COLUMN id SET DEFAULT nextval('public.ajustes_saldo_id_seq'::regclass);


--
-- Name: categorias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);


--
-- Name: categorias_aprendidas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias_aprendidas ALTER COLUMN id SET DEFAULT nextval('public.categorias_aprendidas_id_seq'::regclass);


--
-- Name: utilizadores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilizadores ALTER COLUMN id SET DEFAULT nextval('public.utilizadores_id_seq'::regclass);


--
-- Name: ajustes_saldo ajustes_saldo_conta_id_data_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ajustes_saldo
    ADD CONSTRAINT ajustes_saldo_conta_id_data_key UNIQUE (conta_id, data);


--
-- Name: ajustes_saldo ajustes_saldo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ajustes_saldo
    ADD CONSTRAINT ajustes_saldo_pkey PRIMARY KEY (id);


--
-- Name: categorias_aprendidas categorias_aprendidas_descricao_utilizador_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias_aprendidas
    ADD CONSTRAINT categorias_aprendidas_descricao_utilizador_id_key UNIQUE (descricao, utilizador_id);


--
-- Name: categorias_aprendidas categorias_aprendidas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias_aprendidas
    ADD CONSTRAINT categorias_aprendidas_pkey PRIMARY KEY (id);


--
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- Name: contas contas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contas
    ADD CONSTRAINT contas_pkey PRIMARY KEY (id);


--
-- Name: movimentos movimentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos
    ADD CONSTRAINT movimentos_pkey PRIMARY KEY (id);


--
-- Name: utilizadores utilizadores_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilizadores
    ADD CONSTRAINT utilizadores_email_key UNIQUE (email);


--
-- Name: utilizadores utilizadores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilizadores
    ADD CONSTRAINT utilizadores_pkey PRIMARY KEY (id);


--
-- Name: idx_categorias_utilizador_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_categorias_utilizador_parent ON public.categorias USING btree (utilizador_id, parent_id);


--
-- Name: idx_movimentos_conta; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movimentos_conta ON public.movimentos USING btree (conta_id);


--
-- Name: idx_movimentos_data; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movimentos_data ON public.movimentos USING btree (data);


--
-- Name: idx_movimentos_utilizador_data; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_movimentos_utilizador_data ON public.movimentos USING btree (utilizador_id, data DESC);


--
-- Name: ajustes_saldo ajustes_saldo_conta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ajustes_saldo
    ADD CONSTRAINT ajustes_saldo_conta_id_fkey FOREIGN KEY (conta_id) REFERENCES public.contas(id) ON DELETE CASCADE;


--
-- Name: categorias_aprendidas categorias_aprendidas_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias_aprendidas
    ADD CONSTRAINT categorias_aprendidas_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id);


--
-- Name: categorias_aprendidas categorias_aprendidas_utilizador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias_aprendidas
    ADD CONSTRAINT categorias_aprendidas_utilizador_id_fkey FOREIGN KEY (utilizador_id) REFERENCES public.utilizadores(id);


--
-- Name: categorias categorias_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.categorias(id);


--
-- Name: categorias categorias_utilizador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_utilizador_id_fkey FOREIGN KEY (utilizador_id) REFERENCES public.utilizadores(id);


--
-- Name: contas contas_utilizador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contas
    ADD CONSTRAINT contas_utilizador_id_fkey FOREIGN KEY (utilizador_id) REFERENCES public.utilizadores(id);


--
-- Name: movimentos movimentos_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos
    ADD CONSTRAINT movimentos_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id);


--
-- Name: movimentos movimentos_conta_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos
    ADD CONSTRAINT movimentos_conta_id_fkey FOREIGN KEY (conta_id) REFERENCES public.contas(id);


--
-- Name: movimentos movimentos_utilizador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos
    ADD CONSTRAINT movimentos_utilizador_id_fkey FOREIGN KEY (utilizador_id) REFERENCES public.utilizadores(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 5iQJRYQpXZxlHMZ6CNpoCafRhdrWRAXbwaQZkTaPUHQTuDA6amDrGe3WuOIlOPS

