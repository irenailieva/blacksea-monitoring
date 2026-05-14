--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4 (Debian 15.4-1.pgdg110+1)
-- Dumped by pg_dump version 15.4 (Debian 15.4-1.pgdg110+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger;


ALTER SCHEMA tiger OWNER TO postgres;

--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger_data;


ALTER SCHEMA tiger_data OWNER TO postgres;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO postgres;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: team_role; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.team_role AS ENUM (
    'member',
    'moderator',
    'admin'
);


ALTER TYPE public.team_role OWNER TO postgres;

--
-- Name: user_role; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_role AS ENUM (
    'admin',
    'researcher',
    'viewer'
);


ALTER TYPE public.user_role OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: classification_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.classification_results (
    id integer NOT NULL,
    model_run_id integer,
    scene_id integer NOT NULL,
    region_id integer,
    label character varying(100) NOT NULL,
    confidence double precision,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.classification_results OWNER TO postgres;

--
-- Name: classification_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.classification_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.classification_results_id_seq OWNER TO postgres;

--
-- Name: classification_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.classification_results_id_seq OWNED BY public.classification_results.id;


--
-- Name: error_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.error_logs (
    id integer NOT NULL,
    etl_job_id integer NOT NULL,
    level character varying(20) NOT NULL,
    message text NOT NULL,
    stacktrace text,
    occurred_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.error_logs OWNER TO postgres;

--
-- Name: error_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.error_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.error_logs_id_seq OWNER TO postgres;

--
-- Name: error_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.error_logs_id_seq OWNED BY public.error_logs.id;


--
-- Name: etl_jobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.etl_jobs (
    id integer NOT NULL,
    job_type character varying(50) NOT NULL,
    status character varying(30) NOT NULL,
    started_at timestamp without time zone NOT NULL,
    finished_at timestamp without time zone,
    payload json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.etl_jobs OWNER TO postgres;

--
-- Name: etl_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.etl_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.etl_jobs_id_seq OWNER TO postgres;

--
-- Name: etl_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.etl_jobs_id_seq OWNED BY public.etl_jobs.id;


--
-- Name: index_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.index_types (
    name character varying(50) NOT NULL,
    description text,
    formula character varying(255),
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.index_types OWNER TO postgres;

--
-- Name: index_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.index_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.index_types_id_seq OWNER TO postgres;

--
-- Name: index_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.index_types_id_seq OWNED BY public.index_types.id;


--
-- Name: index_values; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.index_values (
    scene_id integer NOT NULL,
    index_type_id integer NOT NULL,
    region_id integer,
    mean_value double precision,
    min_value double precision,
    max_value double precision,
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.index_values OWNER TO postgres;

--
-- Name: index_values_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.index_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.index_values_id_seq OWNER TO postgres;

--
-- Name: index_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.index_values_id_seq OWNED BY public.index_values.id;


--
-- Name: model_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.model_runs (
    id integer NOT NULL,
    model_name character varying(100) NOT NULL,
    parameters json,
    started_at timestamp without time zone NOT NULL,
    finished_at timestamp without time zone,
    status character varying(30) NOT NULL,
    metrics json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.model_runs OWNER TO postgres;

--
-- Name: model_runs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.model_runs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.model_runs_id_seq OWNER TO postgres;

--
-- Name: model_runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.model_runs_id_seq OWNED BY public.model_runs.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    title character varying(120) NOT NULL,
    message character varying(500) NOT NULL,
    read boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notifications_id_seq OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: regions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.regions (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(255),
    area_km2 double precision,
    geometry public.geometry(Polygon,4326) NOT NULL,
    type character varying(50) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.regions OWNER TO postgres;

--
-- Name: regions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.regions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.regions_id_seq OWNER TO postgres;

--
-- Name: regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.regions_id_seq OWNED BY public.regions.id;


--
-- Name: scene_files; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scene_files (
    id integer NOT NULL,
    scene_id integer NOT NULL,
    file_type character varying(50) NOT NULL,
    path character varying(255) NOT NULL,
    size_bytes integer,
    checksum character varying(64),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.scene_files OWNER TO postgres;

--
-- Name: scene_files_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scene_files_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scene_files_id_seq OWNER TO postgres;

--
-- Name: scene_files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scene_files_id_seq OWNED BY public.scene_files.id;


--
-- Name: scenes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scenes (
    id integer NOT NULL,
    scene_id character varying(100) NOT NULL,
    acquisition_date date NOT NULL,
    satellite character varying(50) NOT NULL,
    cloud_cover double precision,
    tile character varying(20),
    path character varying(255),
    region_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.scenes OWNER TO postgres;

--
-- Name: scenes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scenes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scenes_id_seq OWNER TO postgres;

--
-- Name: scenes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scenes_id_seq OWNED BY public.scenes.id;


--
-- Name: shap_values; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shap_values (
    id integer NOT NULL,
    model_run_id integer NOT NULL,
    scene_id integer NOT NULL,
    index_type_id integer NOT NULL,
    feature_name character varying(100) NOT NULL,
    value double precision NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.shap_values OWNER TO postgres;

--
-- Name: shap_values_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shap_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.shap_values_id_seq OWNER TO postgres;

--
-- Name: shap_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shap_values_id_seq OWNED BY public.shap_values.id;


--
-- Name: team; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.team OWNER TO postgres;

--
-- Name: team_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.team_id_seq OWNER TO postgres;

--
-- Name: team_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_id_seq OWNED BY public.team.id;


--
-- Name: team_membership; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_membership (
    id integer NOT NULL,
    user_id integer NOT NULL,
    team_id integer NOT NULL,
    role public.team_role NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.team_membership OWNER TO postgres;

--
-- Name: team_membership_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_membership_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.team_membership_id_seq OWNER TO postgres;

--
-- Name: team_membership_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_membership_id_seq OWNED BY public.team_membership.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role public.user_role NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public."user" OWNER TO postgres;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO postgres;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: webhook_integrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.webhook_integrations (
    id integer NOT NULL,
    user_id integer NOT NULL,
    provider character varying(50) NOT NULL,
    endpoint_url character varying(255) NOT NULL,
    secret character varying(255),
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.webhook_integrations OWNER TO postgres;

--
-- Name: webhook_integrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.webhook_integrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.webhook_integrations_id_seq OWNER TO postgres;

--
-- Name: webhook_integrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.webhook_integrations_id_seq OWNED BY public.webhook_integrations.id;


--
-- Name: classification_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classification_results ALTER COLUMN id SET DEFAULT nextval('public.classification_results_id_seq'::regclass);


--
-- Name: error_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_logs ALTER COLUMN id SET DEFAULT nextval('public.error_logs_id_seq'::regclass);


--
-- Name: etl_jobs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etl_jobs ALTER COLUMN id SET DEFAULT nextval('public.etl_jobs_id_seq'::regclass);


--
-- Name: index_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_types ALTER COLUMN id SET DEFAULT nextval('public.index_types_id_seq'::regclass);


--
-- Name: index_values id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_values ALTER COLUMN id SET DEFAULT nextval('public.index_values_id_seq'::regclass);


--
-- Name: model_runs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model_runs ALTER COLUMN id SET DEFAULT nextval('public.model_runs_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: regions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.regions ALTER COLUMN id SET DEFAULT nextval('public.regions_id_seq'::regclass);


--
-- Name: scene_files id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_files ALTER COLUMN id SET DEFAULT nextval('public.scene_files_id_seq'::regclass);


--
-- Name: scenes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scenes ALTER COLUMN id SET DEFAULT nextval('public.scenes_id_seq'::regclass);


--
-- Name: shap_values id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shap_values ALTER COLUMN id SET DEFAULT nextval('public.shap_values_id_seq'::regclass);


--
-- Name: team id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team ALTER COLUMN id SET DEFAULT nextval('public.team_id_seq'::regclass);


--
-- Name: team_membership id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_membership ALTER COLUMN id SET DEFAULT nextval('public.team_membership_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: webhook_integrations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webhook_integrations ALTER COLUMN id SET DEFAULT nextval('public.webhook_integrations_id_seq'::regclass);


--
-- Name: classification_results pk_classification_results; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classification_results
    ADD CONSTRAINT pk_classification_results PRIMARY KEY (id);


--
-- Name: error_logs pk_error_logs; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_logs
    ADD CONSTRAINT pk_error_logs PRIMARY KEY (id);


--
-- Name: etl_jobs pk_etl_jobs; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etl_jobs
    ADD CONSTRAINT pk_etl_jobs PRIMARY KEY (id);


--
-- Name: index_types pk_index_types; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_types
    ADD CONSTRAINT pk_index_types PRIMARY KEY (id);


--
-- Name: index_values pk_index_values; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_values
    ADD CONSTRAINT pk_index_values PRIMARY KEY (id);


--
-- Name: model_runs pk_model_runs; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.model_runs
    ADD CONSTRAINT pk_model_runs PRIMARY KEY (id);


--
-- Name: notifications pk_notifications; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT pk_notifications PRIMARY KEY (id);


--
-- Name: regions pk_regions; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT pk_regions PRIMARY KEY (id);


--
-- Name: scene_files pk_scene_files; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_files
    ADD CONSTRAINT pk_scene_files PRIMARY KEY (id);


--
-- Name: scenes pk_scenes; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT pk_scenes PRIMARY KEY (id);


--
-- Name: shap_values pk_shap_values; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shap_values
    ADD CONSTRAINT pk_shap_values PRIMARY KEY (id);


--
-- Name: team pk_team; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team
    ADD CONSTRAINT pk_team PRIMARY KEY (id);


--
-- Name: team_membership pk_team_membership; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_membership
    ADD CONSTRAINT pk_team_membership PRIMARY KEY (id);


--
-- Name: user pk_user; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT pk_user PRIMARY KEY (id);


--
-- Name: webhook_integrations pk_webhook_integrations; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webhook_integrations
    ADD CONSTRAINT pk_webhook_integrations PRIMARY KEY (id);


--
-- Name: index_types uq_index_types_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_types
    ADD CONSTRAINT uq_index_types_name UNIQUE (name);


--
-- Name: regions uq_regions_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT uq_regions_name UNIQUE (name);


--
-- Name: scenes uq_scenes_scene_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT uq_scenes_scene_id UNIQUE (scene_id);


--
-- Name: team uq_team_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team
    ADD CONSTRAINT uq_team_name UNIQUE (name);


--
-- Name: user uq_user_email; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT uq_user_email UNIQUE (email);


--
-- Name: user uq_user_username; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT uq_user_username UNIQUE (username);


--
-- Name: idx_regions_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_regions_geometry ON public.regions USING gist (geometry);


--
-- Name: ix_index_types_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_index_types_id ON public.index_types USING btree (id);


--
-- Name: ix_index_values_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_index_values_id ON public.index_values USING btree (id);


--
-- Name: ix_scenes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scenes_id ON public.scenes USING btree (id);


--
-- Name: classification_results fk_classification_results_model_run_id_model_runs; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classification_results
    ADD CONSTRAINT fk_classification_results_model_run_id_model_runs FOREIGN KEY (model_run_id) REFERENCES public.model_runs(id) ON DELETE SET NULL;


--
-- Name: classification_results fk_classification_results_region_id_regions; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classification_results
    ADD CONSTRAINT fk_classification_results_region_id_regions FOREIGN KEY (region_id) REFERENCES public.regions(id) ON DELETE SET NULL;


--
-- Name: classification_results fk_classification_results_scene_id_scenes; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classification_results
    ADD CONSTRAINT fk_classification_results_scene_id_scenes FOREIGN KEY (scene_id) REFERENCES public.scenes(id) ON DELETE CASCADE;


--
-- Name: error_logs fk_error_logs_etl_job_id_etl_jobs; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_logs
    ADD CONSTRAINT fk_error_logs_etl_job_id_etl_jobs FOREIGN KEY (etl_job_id) REFERENCES public.etl_jobs(id) ON DELETE CASCADE;


--
-- Name: index_values fk_index_values_index_type_id_index_types; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_values
    ADD CONSTRAINT fk_index_values_index_type_id_index_types FOREIGN KEY (index_type_id) REFERENCES public.index_types(id) ON DELETE CASCADE;


--
-- Name: index_values fk_index_values_region_id_regions; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_values
    ADD CONSTRAINT fk_index_values_region_id_regions FOREIGN KEY (region_id) REFERENCES public.regions(id) ON DELETE SET NULL;


--
-- Name: index_values fk_index_values_scene_id_scenes; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.index_values
    ADD CONSTRAINT fk_index_values_scene_id_scenes FOREIGN KEY (scene_id) REFERENCES public.scenes(id) ON DELETE CASCADE;


--
-- Name: notifications fk_notifications_user_id_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT fk_notifications_user_id_user FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: scene_files fk_scene_files_scene_id_scenes; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_files
    ADD CONSTRAINT fk_scene_files_scene_id_scenes FOREIGN KEY (scene_id) REFERENCES public.scenes(id) ON DELETE CASCADE;


--
-- Name: scenes fk_scenes_region_id_regions; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT fk_scenes_region_id_regions FOREIGN KEY (region_id) REFERENCES public.regions(id) ON DELETE RESTRICT;


--
-- Name: shap_values fk_shap_values_index_type_id_index_types; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shap_values
    ADD CONSTRAINT fk_shap_values_index_type_id_index_types FOREIGN KEY (index_type_id) REFERENCES public.index_types(id) ON DELETE CASCADE;


--
-- Name: shap_values fk_shap_values_model_run_id_model_runs; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shap_values
    ADD CONSTRAINT fk_shap_values_model_run_id_model_runs FOREIGN KEY (model_run_id) REFERENCES public.model_runs(id) ON DELETE CASCADE;


--
-- Name: shap_values fk_shap_values_scene_id_scenes; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shap_values
    ADD CONSTRAINT fk_shap_values_scene_id_scenes FOREIGN KEY (scene_id) REFERENCES public.scenes(id) ON DELETE CASCADE;


--
-- Name: team_membership fk_team_membership_team_id_team; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_membership
    ADD CONSTRAINT fk_team_membership_team_id_team FOREIGN KEY (team_id) REFERENCES public.team(id) ON DELETE CASCADE;


--
-- Name: team_membership fk_team_membership_user_id_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_membership
    ADD CONSTRAINT fk_team_membership_user_id_user FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: webhook_integrations fk_webhook_integrations_user_id_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webhook_integrations
    ADD CONSTRAINT fk_webhook_integrations_user_id_user FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--


