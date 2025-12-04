import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Sistema de Cadastro de Cartuchos",
    page_icon="🖨️",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #374151;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10B981;
        margin: 1rem 0;
    }
    .sql-box {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3B82F6;
        margin: 1rem 0;
        font-family: monospace;
    }
    .error-box {
        background-color: #FEE2E2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #EF4444;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuração da conexão com o banco de dados
@st.cache_resource
def init_connection():
    """Inicializa a conexão com o banco de dados"""
    try:
        # CONFIGURE AQUI SUAS CREDENCIAIS DO MYSQL
        # Formato: mysql+pymysql://usuario:senha@host:porta/banco_de_dados
        connection_string = "mysql+pymysql://root:@localhost:3306/db_insumos"
        
        engine = create_engine(connection_string, pool_pre_ping=True)
        return engine
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
        return None

# Inicializar conexão
engine = init_connection()

# Função para verificar se uma coluna existe
def coluna_existe(tabela, coluna):
    """Verifica se uma coluna existe em uma tabela"""
    try:
        inspector = inspect(engine)
        colunas = inspector.get_columns(tabela)
        colunas_nomes = [c['name'] for c in colunas]
        return coluna in colunas_nomes
    except:
        return False

# Função para executar comandos SQL
def executar_sql(query, params=None, fetch=False, show_error=True):
    """Executa comandos SQL usando SQLAlchemy"""
    if engine is None:
        if show_error:
            st.error("❌ Conexão com o banco de dados não estabelecida.")
        return None
    
    try:
        with engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            
            conn.commit()
            
            if fetch:
                # Para SELECT, retornar DataFrame
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df
            else:
                # Para INSERT, UPDATE, DELETE, retornar número de linhas afetadas
                return result.rowcount
                
    except SQLAlchemyError as e:
        if show_error:
            st.error(f"❌ Erro SQL: {str(e)}")
            st.markdown(f"""
            <div class='error-box'>
                <strong>Query:</strong><br>
                <code>{query}</code><br><br>
                <strong>Parâmetros:</strong><br>
                <code>{params}</code>
            </div>
            """, unsafe_allow_html=True)
        return None
    except Exception as e:
        if show_error:
            st.error(f"❌ Erro inesperado: {str(e)}")
        return None

# Função para testar conexão
def testar_conexao():
    """Testa a conexão com o banco de dados"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "✅ Conexão estabelecida com sucesso!"
    except Exception as e:
        return False, f"❌ Erro de conexão: {str(e)}"

# Função para criar tabelas (versão simplificada)
def criar_tabelas():
    """Cria as tabelas necessárias se não existirem"""
    
    tabelas_sql = [
        # Tabela fabricantes
        """CREATE TABLE IF NOT EXISTS fabricantes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL
        )""",
        
        # Tabela cores_referencia
        """CREATE TABLE IF NOT EXISTS cores_referencia (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(50) NOT NULL,
            codigo_hex VARCHAR(7)
        )""",
        
        # Tabela capacidades
        """CREATE TABLE IF NOT EXISTS capacidades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            capacidade_ml INT NOT NULL
        )""",
        
        # Tabela modelos_impressora
        """CREATE TABLE IF NOT EXISTS modelos_impressora (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(150) NOT NULL,
            fabricante_id INT,
            FOREIGN KEY (fabricante_id) REFERENCES fabricantes(id)
        )""",
        
        # Tabela cartuchos
        """CREATE TABLE IF NOT EXISTS cartuchos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            modelo_cartucho VARCHAR(100) NOT NULL,
            cor_id INT,
            modelo_impressora_id INT,
            codigo_referencia VARCHAR(50),
            FOREIGN KEY (cor_id) REFERENCES cores_referencia(id),
            FOREIGN KEY (modelo_impressora_id) REFERENCES modelos_impressora(id)
        )""",
        
        # Tabela cartucho_capacidades
        """CREATE TABLE IF NOT EXISTS cartucho_capacidades (
            cartucho_id INT,
            capacidade_id INT,
            PRIMARY KEY (cartucho_id, capacidade_id),
            FOREIGN KEY (cartucho_id) REFERENCES cartuchos(id) ON DELETE CASCADE,
            FOREIGN KEY (capacidade_id) REFERENCES capacidades(id)
        )"""
    ]
    
    resultados = []
    for i, sql in enumerate(tabelas_sql):
        try:
            executar_sql(sql, show_error=False)
            nome_tabela = ['fabricantes', 'cores_referencia', 'capacidades', 
                          'modelos_impressora', 'cartuchos', 'cartucho_capacidades'][i]
            resultados.append(f"✅ Tabela '{nome_tabela}' verificada/criada")
        except Exception as e:
            nome_tabela = ['fabricantes', 'cores_referencia', 'capacidades', 
                          'modelos_impressora', 'cartuchos', 'cartucho_capacidades'][i]
            resultados.append(f"❌ Erro na tabela '{nome_tabela}': {str(e)}")
    
    return resultados

# Função para inserir dados iniciais
def inserir_dados_iniciais():
    """Insere dados iniciais nas tabelas"""
    dados_iniciais = [
        # Fabricantes
        "INSERT IGNORE INTO fabricantes (nome) VALUES ('Epson')",
        "INSERT IGNORE INTO fabricantes (nome) VALUES ('HP')",
        "INSERT IGNORE INTO fabricantes (nome) VALUES ('Canon')",
        "INSERT IGNORE INTO fabricantes (nome) VALUES ('Brother')",
        
        # Cores
        "INSERT IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Black', '#000000')",
        "INSERT IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Cyan', '#00FFFF')",
        "INSERT IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Magenta', '#FF00FF')",
        "INSERT IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Yellow', '#FFFF00')",
        
        # Capacidades
        "INSERT IGNORE INTO capacidades (capacidade_ml) VALUES (100)",
        "INSERT IGNORE INTO capacidades (capacidade_ml) VALUES (250)",
        "INSERT IGNORE INTO capacidades (capacidade_ml) VALUES (500)",
        "INSERT IGNORE INTO capacidades (capacidade_ml) VALUES (1000)"
    ]
    
    for sql in dados_iniciais:
        executar_sql(sql, show_error=False)

# Menu lateral
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208720.png", width=100)
    st.markdown("## 🖨️ Sistema de Cartuchos")
    
    # Testar conexão
    if st.button("🔗 Testar Conexão", use_container_width=True):
        sucesso, mensagem = testar_conexao()
        if sucesso:
            st.success(mensagem)
        else:
            st.error(mensagem)
    
    # Inicializar banco
    if st.button("🔄 Inicializar Banco", use_container_width=True):
        with st.spinner("Criando tabelas..."):
            resultados = criar_tabelas()
            for resultado in resultados:
                st.write(resultado)
        
        with st.spinner("Inserindo dados iniciais..."):
            inserir_dados_iniciais()
            st.success("✅ Dados iniciais inseridos!")
    
    st.divider()
    
    selected = option_menu(
        menu_title="Menu Principal",
        options=["📊 Dashboard", "📝 Cadastros", "🔍 Consultas", "⚙️ Configurações", "🗄️ SQL Executor"],
        icons=["house", "pencil-square", "search", "gear", "terminal"],
        menu_icon="cast",
        default_index=0,
    )

# ===== PÁGINA: DASHBOARD =====
if selected == "📊 Dashboard":
    st.markdown("<h1 class='main-header'>📊 Dashboard - Sistema de Cartuchos</h1>", unsafe_allow_html=True)
    
    # Testar conexão primeiro
    sucesso, mensagem = testar_conexao()
    if not sucesso:
        st.error(mensagem)
        st.stop()
    
    # Estatísticas com SQL direto
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        query = "SELECT COUNT(*) as total FROM fabricantes"
        result = executar_sql(query, fetch=True)
        total = result.iloc[0]['total'] if result is not None and not result.empty else 0
        st.metric("Fabricantes", total)
    
    with col2:
        query = "SELECT COUNT(*) as total FROM modelos_impressora"
        result = executar_sql(query, fetch=True)
        total = result.iloc[0]['total'] if result is not None and not result.empty else 0
        st.metric("Modelos Impressora", total)
    
    with col3:
        query = "SELECT COUNT(*) as total FROM cores_referencia"
        result = executar_sql(query, fetch=True)
        total = result.iloc[0]['total'] if result is not None and not result.empty else 0
        st.metric("Cores", total)
    
    with col4:
        query = "SELECT COUNT(*) as total FROM cartuchos"
        result = executar_sql(query, fetch=True)
        total = result.iloc[0]['total'] if result is not None and not result.empty else 0
        st.metric("Cartuchos", total)
    
    st.divider()
    
    # Gráfico de cartuchos por cor
    st.markdown("<h3 class='sub-header'>Cartuchos por Cor</h3>", unsafe_allow_html=True)
    
    query = """
        SELECT cr.nome as cor, COUNT(c.id) as quantidade
        FROM cartuchos c
        JOIN cores_referencia cr ON c.cor_id = cr.id
        GROUP BY cr.nome
        ORDER BY quantidade DESC
    """
    cartuchos_por_cor = executar_sql(query, fetch=True)
    
    if cartuchos_por_cor is not None and not cartuchos_por_cor.empty:
        st.bar_chart(cartuchos_por_cor.set_index('cor'))
        with st.expander("📊 Ver Dados Detalhados"):
            st.dataframe(cartuchos_por_cor)
    else:
        st.info("Nenhum cartucho cadastrado ainda.")

# ===== PÁGINA: CADASTROS =====
elif selected == "📝 Cadastros":
    st.markdown("<h1 class='main-header'>📝 Cadastro de Itens</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🖨️ Fabricantes", 
        "🖨️ Modelos Impressora", 
        "🎨 Cores", 
        "📦 Capacidades", 
        "🖨️ Cartuchos"
    ])
    
    # TAB 1: Fabricantes
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<h3 class='sub-header'>Cadastrar Novo</h3>", unsafe_allow_html=True)
            
            with st.form("form_fabricante", clear_on_submit=True):
                nome_fabricante = st.text_input("Nome do Fabricante", placeholder="Ex: Epson, HP, Canon")
                submitted = st.form_submit_button("✅ Cadastrar Fabricante")
                
                if submitted and nome_fabricante:
                    query = "INSERT INTO fabricantes (nome) VALUES (:nome)"
                    resultado = executar_sql(query, params={"nome": nome_fabricante})
                    if resultado is not None:
                        st.success(f"✅ Fabricante '{nome_fabricante}' cadastrado com sucesso!")
                        st.markdown(f"""
                        <div class='sql-box'>
                            SQL Executado:<br>
                            INSERT INTO fabricantes (nome) VALUES ('{nome_fabricante}')
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3 class='sub-header'>Fabricantes Cadastrados</h3>", unsafe_allow_html=True)
            # Query simplificada sem data_criacao
            query = "SELECT id, nome FROM fabricantes ORDER BY nome"
            fabricantes_df = executar_sql(query, fetch=True)
            
            if fabricantes_df is not None and not fabricantes_df.empty:
                st.dataframe(fabricantes_df, use_container_width=True, hide_index=True)
                
                # Opção de excluir
                with st.expander("🗑️ Gerenciar Fabricantes"):
                    fabricante_excluir = st.selectbox(
                        "Selecione o fabricante para excluir:",
                        options=fabricantes_df['nome'].tolist(),
                        key="excluir_fabricante"
                    )
                    
                    if st.button("Excluir Fabricante", type="secondary"):
                        # Verificar se o fabricante está sendo usado
                        query_check = "SELECT COUNT(*) FROM modelos_impressora WHERE fabricante_id IN (SELECT id FROM fabricantes WHERE nome = :nome)"
                        check_result = executar_sql(query_check, params={"nome": fabricante_excluir}, fetch=True)
                        
                        if check_result is not None and check_result.iloc[0][0] > 0:
                            st.error(f"Não é possível excluir '{fabricante_excluir}' porque existem modelos de impressora associados.")
                        else:
                            query = "DELETE FROM fabricantes WHERE nome = :nome"
                            if executar_sql(query, params={"nome": fabricante_excluir}):
                                st.warning(f"Fabricante '{fabricante_excluir}' excluído!")
                                st.rerun()
            else:
                st.info("Nenhum fabricante cadastrado.")
    
    # TAB 2: Modelos de Impressora
    with tab2:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<h3 class='sub-header'>Cadastrar Novo Modelo</h3>", unsafe_allow_html=True)
            
            # Buscar fabricantes para o select
            query_fabricantes = "SELECT id, nome FROM fabricantes ORDER BY nome"
            fabricantes_df = executar_sql(query_fabricantes, fetch=True)
            
            if fabricantes_df is not None and not fabricantes_df.empty:
                fabricantes_opcoes = {row['nome']: row['id'] for _, row in fabricantes_df.iterrows()}
                
                with st.form("form_modelo_impressora", clear_on_submit=True):
                    nome_modelo = st.text_input("Nome do Modelo", placeholder="Ex: Epson Tx410")
                    fabricante_selecionado = st.selectbox("Fabricante", options=list(fabricantes_opcoes.keys()))
                    submitted = st.form_submit_button("✅ Cadastrar Modelo")
                    
                    if submitted and nome_modelo:
                        fabricante_id = fabricantes_opcoes[fabricante_selecionado]
                        query = "INSERT INTO modelos_impressora (nome, fabricante_id) VALUES (:nome, :fabricante_id)"
                        if executar_sql(query, params={"nome": nome_modelo, "fabricante_id": fabricante_id}):
                            st.success(f"✅ Modelo '{nome_modelo}' cadastrado com sucesso!")
                            st.markdown(f"""
                            <div class='sql-box'>
                                SQL Executado:<br>
                                INSERT INTO modelos_impressora (nome, fabricante_id) VALUES ('{nome_modelo}', {fabricante_id})
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.warning("Cadastre primeiro um fabricante na aba 'Fabricantes'")
        
        with col2:
            st.markdown("<h3 class='sub-header'>Modelos Cadastrados</h3>", unsafe_allow_html=True)
            query = """
                SELECT mi.id, mi.nome, f.nome as fabricante
                FROM modelos_impressora mi
                JOIN fabricantes f ON mi.fabricante_id = f.id
                ORDER BY mi.nome
            """
            modelos_df = executar_sql(query, fetch=True)
            
            if modelos_df is not None and not modelos_df.empty:
                st.dataframe(modelos_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum modelo de impressora cadastrado.")
    
    # TAB 3: Cores
    with tab3:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<h3 class='sub-header'>Cadastrar Nova Cor</h3>", unsafe_allow_html=True)
            
            with st.form("form_cor", clear_on_submit=True):
                nome_cor = st.text_input("Nome da Cor", placeholder="Ex: Black, Cyan, Magenta")
                codigo_hex = st.color_picker("Código Hex", "#000000")
                submitted = st.form_submit_button("✅ Cadastrar Cor")
                
                if submitted and nome_cor:
                    query = "INSERT INTO cores_referencia (nome, codigo_hex) VALUES (:nome, :codigo_hex)"
                    if executar_sql(query, params={"nome": nome_cor, "codigo_hex": codigo_hex}):
                        st.success(f"✅ Cor '{nome_cor}' cadastrada com sucesso!")
                        st.markdown(f"""
                        <div class='sql-box'>
                            SQL Executado:<br>
                            INSERT INTO cores_referencia (nome, codigo_hex) VALUES ('{nome_cor}', '{codigo_hex}')
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3 class='sub-header'>Cores Cadastradas</h3>", unsafe_allow_html=True)
            query = "SELECT id, nome, codigo_hex FROM cores_referencia ORDER BY nome"
            cores_df = executar_sql(query, fetch=True)
            
            if cores_df is not None and not cores_df.empty:
                st.dataframe(cores_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma cor cadastrada.")
    
    # TAB 4: Capacidades
    with tab4:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<h3 class='sub-header'>Cadastrar Nova Capacidade</h3>", unsafe_allow_html=True)
            
            with st.form("form_capacidade", clear_on_submit=True):
                capacidade_ml = st.number_input("Capacidade (ml)", min_value=1, step=1, value=100)
                submitted = st.form_submit_button("✅ Cadastrar Capacidade")
                
                if submitted:
                    query = "INSERT INTO capacidades (capacidade_ml) VALUES (:capacidade)"
                    if executar_sql(query, params={"capacidade": int(capacidade_ml)}):
                        st.success(f"✅ Capacidade de {capacidade_ml}ml cadastrada com sucesso!")
                        st.markdown(f"""
                        <div class='sql-box'>
                            SQL Executado:<br>
                            INSERT INTO capacidades (capacidade_ml) VALUES ({capacidade_ml})
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3 class='sub-header'>Capacidades Cadastradas</h3>", unsafe_allow_html=True)
            query = "SELECT id, capacidade_ml FROM capacidades ORDER BY capacidade_ml"
            capacidades_df = executar_sql(query, fetch=True)
            
            if capacidades_df is not None and not capacidades_df.empty:
                st.dataframe(capacidades_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma capacidade cadastrada.")
    
    # TAB 5: Cartuchos
    with tab5:
        st.markdown("<h3 class='sub-header'>Cadastrar Novo Cartucho</h3>", unsafe_allow_html=True)
        
        # Carregar dados para selects
        cores_query = "SELECT id, nome FROM cores_referencia ORDER BY nome"
        modelos_query = "SELECT id, nome FROM modelos_impressora ORDER BY nome"
        capacidades_query = "SELECT id, capacidade_ml FROM capacidades ORDER BY capacidade_ml"
        
        cores_df = executar_sql(cores_query, fetch=True)
        modelos_df = executar_sql(modelos_query, fetch=True)
        capacidades_df = executar_sql(capacidades_query, fetch=True)
        
        if (cores_df is not None and not cores_df.empty and 
            modelos_df is not None and not modelos_df.empty and 
            capacidades_df is not None and not capacidades_df.empty):
            
            with st.form("form_cartucho", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    modelo_cartucho = st.text_input("Modelo do Cartucho*", placeholder="Ex: 1073120 Black")
                    codigo_referencia = st.text_input("Código de Referência", placeholder="Ex: 1073120")
                
                with col2:
                    cor_selecionada = st.selectbox("Cor*", options=cores_df['nome'].tolist())
                    modelo_selecionado = st.selectbox("Modelo de Impressora*", options=modelos_df['nome'].tolist())
                
                # Seleção múltipla de capacidades
                capacidades_opcoes = capacidades_df['capacidade_ml'].astype(str) + "ml"
                capacidades_selecionadas = st.multiselect(
                    "Capacidades Disponíveis",
                    options=capacidades_opcoes.tolist(),
                    default=capacidades_opcoes.tolist()[:2] if len(capacidades_opcoes) > 1 else capacidades_opcoes.tolist()
                )
                
                submitted = st.form_submit_button("✅ Cadastrar Cartucho")
                
                if submitted and modelo_cartucho:
                    # Obter IDs
                    cor_id = int(cores_df[cores_df['nome'] == cor_selecionada].iloc[0]['id'])
                    modelo_id = int(modelos_df[modelos_df['nome'] == modelo_selecionado].iloc[0]['id'])
                    
                    # Inserir cartucho
                    query_cartucho = """
                        INSERT INTO cartuchos (modelo_cartucho, cor_id, modelo_impressora_id, codigo_referencia)
                        VALUES (:modelo, :cor_id, :modelo_id, :codigo)
                    """
                    
                    try:
                        with engine.connect() as conn:
                            # Inserir cartucho e obter o ID
                            result = conn.execute(
                                text(query_cartucho),
                                {
                                    "modelo": modelo_cartucho,
                                    "cor_id": cor_id,
                                    "modelo_id": modelo_id,
                                    "codigo": codigo_referencia
                                }
                            )
                            cartucho_id = result.lastrowid
                            conn.commit()
                        
                        # Associar capacidades
                        for cap_str in capacidades_selecionadas:
                            capacidade_ml = int(cap_str.replace("ml", ""))
                            capacidade_id = int(capacidades_df[capacidades_df['capacidade_ml'] == capacidade_ml].iloc[0]['id'])
                            query_associar = """
                                INSERT INTO cartucho_capacidades (cartucho_id, capacidade_id)
                                VALUES (:cartucho_id, :capacidade_id)
                            """
                            executar_sql(query_associar, params={"cartucho_id": cartucho_id, "capacidade_id": capacidade_id})
                        
                        st.success(f"✅ Cartucho '{modelo_cartucho}' cadastrado com sucesso!")
                        
                        # Mostrar SQL executado
                        sql_executado = f"""
                            INSERT INTO cartuchos (modelo_cartucho, cor_id, modelo_impressora_id, codigo_referencia)
                            VALUES ('{modelo_cartucho}', {cor_id}, {modelo_id}, '{codigo_referencia}')
                        """
                        
                        if capacidades_selecionadas:
                            sql_executado += "\n\nINSERTs em cartucho_capacidades:"
                            for cap_str in capacidades_selecionadas:
                                capacidade_ml = int(cap_str.replace("ml", ""))
                                capacidade_id = int(capacidades_df[capacidades_df['capacidade_ml'] == capacidade_ml].iloc[0]['id'])
                                sql_executado += f"\nINSERT INTO cartucho_capacidades VALUES ({cartucho_id}, {capacidade_id})"
                        
                        st.markdown(f"""
                        <div class='sql-box'>
                            SQL Executado:<br>
                            {sql_executado}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
        else:
            st.warning("⚠️ Cadastre primeiro Cores, Modelos e Capacidades nas abas anteriores.")
        
        st.divider()
        # Listar cartuchos existentes
        st.markdown("<h3 class='sub-header'>Cartuchos Cadastrados</h3>", unsafe_allow_html=True)
        query = """
            SELECT 
                c.id,
                c.modelo_cartucho,
                c.codigo_referencia,
                cr.nome as cor,
                mi.nome as modelo_impressora,
                f.nome as fabricante,
                GROUP_CONCAT(cap.capacidade_ml ORDER BY cap.capacidade_ml SEPARATOR ', ') as capacidades
            FROM cartuchos c
            JOIN cores_referencia cr ON c.cor_id = cr.id
            JOIN modelos_impressora mi ON c.modelo_impressora_id = mi.id
            JOIN fabricantes f ON mi.fabricante_id = f.id
            LEFT JOIN cartucho_capacidades cc ON c.id = cc.cartucho_id
            LEFT JOIN capacidades cap ON cc.capacidade_id = cap.id
            GROUP BY c.id
            ORDER BY c.modelo_cartucho
        """
        cartuchos_df = executar_sql(query, fetch=True)
        
        if cartuchos_df is not None and not cartuchos_df.empty:
            st.dataframe(cartuchos_df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum cartucho cadastrado.")

# ===== PÁGINA: CONSULTAS =====
elif selected == "🔍 Consultas":
    st.markdown("<h1 class='main-header'>🔍 Consulta de Cartuchos</h1>", unsafe_allow_html=True)
    
    # Consulta SQL personalizada
    with st.expander("🔧 Consulta SQL Personalizada"):
        sql_query = st.text_area(
            "Digite sua consulta SQL:",
            value="SELECT * FROM fabricantes LIMIT 10",
            height=100
        )
        
        if st.button("Executar Consulta", key="executar_sql"):
            result = executar_sql(sql_query, fetch=True)
            if result is not None:
                st.dataframe(result, use_container_width=True)
                st.success(f"✅ {len(result)} registros encontrados")
    
    st.divider()
    
    # Filtros avançados
    st.markdown("<h3 class='sub-header'>Filtros Avançados</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cores_df = executar_sql("SELECT nome FROM cores_referencia ORDER BY nome", fetch=True)
        cores_lista = ["Todos"] + cores_df['nome'].tolist() if cores_df is not None else ["Todos"]
        filtro_cor = st.selectbox("Filtrar por Cor", options=cores_lista)
    
    with col2:
        fabricantes_df = executar_sql("SELECT nome FROM fabricantes ORDER BY nome", fetch=True)
        fabricantes_lista = ["Todos"] + fabricantes_df['nome'].tolist() if fabricantes_df is not None else ["Todos"]
        filtro_fabricante = st.selectbox("Filtrar por Fabricante", options=fabricantes_lista)
    
    with col3:
        capacidades_df = executar_sql("SELECT capacidade_ml FROM capacidades ORDER BY capacidade_ml", fetch=True)
        if capacidades_df is not None:
            capacidades_lista = ["Todas"] + (capacidades_df['capacidade_ml'].astype(str) + "ml").tolist()
        else:
            capacidades_lista = ["Todas"]
        filtro_capacidade = st.selectbox("Filtrar por Capacidade", options=capacidades_lista)
    
    # Construir query dinamicamente
    if st.button("🔍 Aplicar Filtros", type="primary"):
        query_base = """
            SELECT 
                c.modelo_cartucho,
                c.codigo_referencia,
                cr.nome as cor,
                mi.nome as modelo_impressora,
                f.nome as fabricante,
                GROUP_CONCAT(cap.capacidade_ml ORDER BY cap.capacidade_ml SEPARATOR ', ') as capacidades
            FROM cartuchos c
            JOIN cores_referencia cr ON c.cor_id = cr.id
            JOIN modelos_impressora mi ON c.modelo_impressora_id = mi.id
            JOIN fabricantes f ON mi.fabricante_id = f.id
            LEFT JOIN cartucho_capacidades cc ON c.id = cc.cartucho_id
            LEFT JOIN capacidades cap ON cc.capacidade_id = cap.id
            WHERE 1=1
        """
        
        params = {}
        param_count = 1
        
        if filtro_cor != "Todos":
            query_base += f" AND cr.nome = :param{param_count}"
            params[f"param{param_count}"] = filtro_cor
            param_count += 1
        
        if filtro_fabricante != "Todos":
            query_base += f" AND f.nome = :param{param_count}"
            params[f"param{param_count}"] = filtro_fabricante
            param_count += 1
        
        if filtro_capacidade != "Todas":
            capacidade_ml = int(filtro_capacidade.replace("ml", ""))
            query_base += f" AND cap.capacidade_ml = :param{param_count}"
            params[f"param{param_count}"] = capacidade_ml
        
        query_base += " GROUP BY c.id ORDER BY c.modelo_cartucho"
        
        # Mostrar query gerada
        st.markdown(f"""
        <div class='sql-box'>
            SQL Gerado:<br>
            {query_base}<br>
            Parâmetros: {params}
        </div>
        """, unsafe_allow_html=True)
        
        resultados = executar_sql(query_base, params=params if params else None, fetch=True)
        
        if resultados is not None and not resultados.empty:
            st.markdown(f"### 📋 Resultados da Pesquisa ({len(resultados)} encontrados)")
            st.dataframe(resultados, use_container_width=True, hide_index=True)
            
            # Opção de exportação
            csv = resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar para CSV",
                data=csv,
                file_name="cartuchos_filtrados.csv",
                mime="text/csv"
            )
        else:
            st.warning("Nenhum cartucho encontrado com os filtros selecionados.")

# ===== PÁGINA: SQL EXECUTOR =====
elif selected == "🗄️ SQL Executor":
    st.markdown("<h1 class='main-header'>🗄️ SQL Executor</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sql_code = st.text_area(
            "Digite seu comando SQL:",
            value="SELECT * FROM fabricantes LIMIT 5;",
            height=200,
            placeholder="Ex: SELECT * FROM tabela WHERE condicao;"
        )
    
    with col2:
        st.markdown("### Tipos de Comandos")
        st.write("""
        **SELECT**: Consultar dados  
        **INSERT**: Inserir dados  
        **UPDATE**: Atualizar dados  
        **DELETE**: Excluir dados  
        **CREATE**: Criar tabelas  
        **DROP**: Excluir tabelas
        """)
        
        tipo_comando = st.selectbox(
            "Tipo de Comando:",
            ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TRUNCATE"]
        )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Executar SQL", type="primary"):
            if sql_code.strip():
                with st.spinner("Executando..."):
                    try:
                        # Verificar se é SELECT ou outro comando
                        if sql_code.strip().upper().startswith('SELECT'):
                            result = executar_sql(sql_code, fetch=True)
                            if result is not None:
                                st.success(f"✅ Comando executado! {len(result)} registros retornados.")
                                st.dataframe(result, use_container_width=True)
                        else:
                            # Para INSERT, UPDATE, DELETE, etc.
                            resultado = executar_sql(sql_code)
                            if resultado is not None:
                                st.success(f"✅ Comando executado com sucesso! {resultado} linha(s) afetada(s).")
                                st.rerun()
                        
                        # Mostrar o SQL executado
                        st.markdown(f"""
                        <div class='sql-box'>
                            SQL Executado:<br>
                            {sql_code}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    with col2:
        if st.button("📋 Exemplos SQL"):
            exemplos = {
                "Consultas básicas": [
                    "SELECT * FROM fabricantes;",
                    "SELECT nome FROM cores_referencia ORDER BY nome;",
                    "SELECT COUNT(*) as total FROM cartuchos;"
                ],
                "Joins complexos": [
                    """SELECT c.modelo_cartucho, cr.nome as cor, f.nome as fabricante
                       FROM cartuchos c
                       JOIN cores_referencia cr ON c.cor_id = cr.id
                       JOIN modelos_impressora mi ON c.modelo_impressora_id = mi.id
                       JOIN fabricantes f ON mi.fabricante_id = f.id
                       LIMIT 10;"""
                ],
                "Inserir dados": [
                    "INSERT INTO fabricantes (nome) VALUES ('Novo Fabricante');",
                    "INSERT INTO cores_referencia (nome, codigo_hex) VALUES ('Laranja', '#FFA500');"
                ]
            }
            
            for categoria, queries in exemplos.items():
                with st.expander(categoria):
                    for query in queries:
                        st.code(query, language="sql")
    
    with col3:
        if st.button("🔄 Limpar"):
            st.rerun()
    
    st.divider()
    
    # Estrutura do banco
    st.markdown("<h3 class='sub-header'>📋 Estrutura do Banco</h3>", unsafe_allow_html=True)
    
    # Listar tabelas
    try:
        inspector = inspect(engine)
        tabelas = inspector.get_table_names()
        
        if tabelas:
            for tabela in tabelas:
                with st.expander(f"📁 {tabela}"):
                    try:
                        colunas = inspector.get_columns(tabela)
                        colunas_info = []
                        for coluna in colunas:
                            colunas_info.append({
                                'Nome': coluna['name'],
                                'Tipo': str(coluna['type']),
                                'Nullable': coluna['nullable'],
                                'Primary Key': coluna.get('primary_key', False)
                            })
                        st.dataframe(pd.DataFrame(colunas_info))
                        
                        # Mostrar dados de exemplo
                        dados_exemplo = executar_sql(f"SELECT * FROM {tabela} LIMIT 5", fetch=True)
                        if dados_exemplo is not None and not dados_exemplo.empty:
                            st.write(f"**Dados de exemplo (5 primeiros registros):**")
                            st.dataframe(dados_exemplo, hide_index=True)
                    except Exception as e:
                        st.error(f"Erro ao obter estrutura da tabela: {str(e)}")
        else:
            st.info("Nenhuma tabela encontrada no banco de dados.")
    except Exception as e:
        st.error(f"❌ Erro ao listar estrutura: {str(e)}")

# ===== PÁGINA: CONFIGURAÇÕES =====
elif selected == "⚙️ Configurações":
    st.markdown("<h1 class='main-header'>⚙️ Configurações do Sistema</h1>", unsafe_allow_html=True)
    
    # Configuração de conexão
    st.markdown("### 🔧 Configuração de Conexão")
    
    with st.expander("Ver Configuração Atual"):
        st.info("""
        Esta aplicação usa SQLAlchemy para conexão com MySQL.
        
        String de conexão atual:
        ```python
        mysql+pymysql://root:@localhost:3306/db_insumos
        ```
        
        Para alterar, modifique a função `init_connection()` no código.
        """)
    
    # Testar conexão
    if st.button("🔗 Testar Conexão Novamente"):
        sucesso, mensagem = testar_conexao()
        if sucesso:
            st.success(mensagem)
        else:
            st.error(mensagem)
    
    st.divider()
    
    # Estatísticas
    st.markdown("### 📊 Estatísticas do Banco")
    
    # Query para estatísticas detalhadas
    estatisticas_query = """
        SELECT 
            (SELECT COUNT(*) FROM fabricantes) as fabricantes,
            (SELECT COUNT(*) FROM modelos_impressora) as modelos,
            (SELECT COUNT(*) FROM cores_referencia) as cores,
            (SELECT COUNT(*) FROM capacidades) as capacidades,
            (SELECT COUNT(*) FROM cartuchos) as cartuchos,
            (SELECT COUNT(*) FROM cartucho_capacidades) as associacoes
    """
    
    estatisticas = executar_sql(estatisticas_query, fetch=True)
    
    if estatisticas is not None:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fabricantes", estatisticas.iloc[0]['fabricantes'])
            st.metric("Modelos", estatisticas.iloc[0]['modelos'])
        
        with col2:
            st.metric("Cores", estatisticas.iloc[0]['cores'])
            st.metric("Capacidades", estatisticas.iloc[0]['capacidades'])
        
        with col3:
            st.metric("Cartuchos", estatisticas.iloc[0]['cartuchos'])
            st.metric("Associações", estatisticas.iloc[0]['associacoes'])
    else:
        st.warning("Não foi possível obter estatísticas do banco.")
    
    st.divider()
    
    # Backup de dados
    st.markdown("### 💾 Backup de Dados")
    
    if st.button("📤 Gerar Backup SQL"):
        # Gerar script SQL de backup
        backup_sql = "-- Backup do Sistema de Cartuchos\n-- Data: " + pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S") + "\n\n"
        
        # Obter todas as tabelas
        inspector = inspect(engine)
        tabelas = inspector.get_table_names()
        
        for tabela in tabelas:
            # Dados da tabela
            dados = executar_sql(f"SELECT * FROM {tabela}", fetch=True)
            if dados is not None and not dados.empty:
                backup_sql += f"\n-- Dados da tabela: {tabela}\n"
                
                # Gerar INSERTs
                for _, row in dados.iterrows():
                    colunas = ', '.join(row.index)
                    valores = []
                    for v in row.values:
                        if pd.isna(v):  # Tratar valores NaN
                            valores.append('NULL')
                        elif isinstance(v, str):
                            # Escapar aspas simples
                            v_escaped = v.replace("'", "''")
                            valores.append(f"'{v_escaped}'")
                        elif isinstance(v, (int, float)):
                            valores.append(str(v))
                        elif v is None:
                            valores.append('NULL')
                        else:
                            valores.append(f"'{str(v)}'")
                    
                    valores_str = ', '.join(valores)
                    backup_sql += f"INSERT INTO {tabela} ({colunas}) VALUES ({valores_str});\n"
        
        # Mostrar e permitir download
        st.download_button(
            label="📥 Download Backup.sql",
            data=backup_sql,
            file_name=f"backup_cartuchos_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.sql",
            mime="text/plain"
        )
        
        with st.expander("📝 Visualizar Backup"):
            st.code(backup_sql, language="sql")
    
    # Limpar cache
    st.divider()
    if st.button("🗑️ Limpar Cache da Aplicação"):
        st.cache_resource.clear()
        st.success("✅ Cache limpo!")
        st.rerun()

# ===== RODAPÉ =====
st.divider()
st.markdown("""
<div style='text-align: center; color: #6B7280; padding: 1rem;'>
    🖨️ Sistema de Gerenciamento de Cartuchos | Desenvolvido com Streamlit + SQLAlchemy + MySQL
</div>
""", unsafe_allow_html=True)