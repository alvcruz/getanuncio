import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

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
    .menu-btn {
        width: 100%;
        text-align: left;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        background-color: white;
        cursor: pointer;
    }
    .menu-btn:hover {
        background-color: #F3F4F6;
    }
    .menu-btn.active {
        background-color: #3B82F6;
        color: white;
        border-color: #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Configuração do banco de dados SQLite
DB_PATH = "cartuchos.db"

def get_connection():
    """Retorna uma conexão com o banco SQLite"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def executar_sql(query, params=None, fetch=False, show_error=True):
    """Executa comandos SQL no SQLite"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        
        if fetch:
            # Para SELECT, retornar DataFrame
            columns = [description[0] for description in cursor.description] if cursor.description else []
            data = cursor.fetchall()
            if data:
                df = pd.DataFrame(data, columns=columns)
            else:
                df = pd.DataFrame(columns=columns)
            cursor.close()
            conn.close()
            return df
        else:
            # Para INSERT, UPDATE, DELETE, retornar número de linhas afetadas
            rowcount = cursor.rowcount
            cursor.close()
            conn.close()
            return rowcount
            
    except Exception as e:
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

def criar_tabelas():
    """Cria as tabelas necessárias no SQLite"""
    
    tabelas_sql = [
        # Tabela fabricantes
        """CREATE TABLE IF NOT EXISTS fabricantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabela cores_referencia
        """CREATE TABLE IF NOT EXISTS cores_referencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            codigo_hex TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabela capacidades
        """CREATE TABLE IF NOT EXISTS capacidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capacidade_ml INTEGER NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabela modelos_impressora
        """CREATE TABLE IF NOT EXISTS modelos_impressora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            fabricante_id INTEGER,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fabricante_id) REFERENCES fabricantes(id)
        )""",
        
        # Tabela cartuchos
        """CREATE TABLE IF NOT EXISTS cartuchos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo_cartucho TEXT NOT NULL,
            cor_id INTEGER,
            modelo_impressora_id INTEGER,
            codigo_referencia TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cor_id) REFERENCES cores_referencia(id),
            FOREIGN KEY (modelo_impressora_id) REFERENCES modelos_impressora(id)
        )""",
        
        # Tabela cartucho_capacidades
        """CREATE TABLE IF NOT EXISTS cartucho_capacidades (
            cartucho_id INTEGER,
            capacidade_id INTEGER,
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

def inserir_dados_iniciais():
    """Insere dados iniciais nas tabelas"""
    dados_iniciais = [
        # Fabricantes
        "INSERT OR IGNORE INTO fabricantes (nome) VALUES ('Epson')",
        "INSERT OR IGNORE INTO fabricantes (nome) VALUES ('HP')",
        "INSERT OR IGNORE INTO fabricantes (nome) VALUES ('Canon')",
        "INSERT OR IGNORE INTO fabricantes (nome) VALUES ('Brother')",
        "INSERT OR IGNORE INTO fabricantes (nome) VALUES ('Lexmark')",
        "INSERT OR IGNORE INTO fabricantes (nome) VALUES ('Xerox')",
        
        # Cores
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Black', '#000000')",
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Cyan', '#00FFFF')",
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Magenta', '#FF00FF')",
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Yellow', '#FFFF00')",
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Light Cyan', '#88FFFF')",
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Light Magenta', '#FF88FF')",
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Gray', '#808080')",
        "INSERT OR IGNORE INTO cores_referencia (nome, codigo_hex) VALUES ('Light Gray', '#D3D3D3')",
        
        # Capacidades
        "INSERT OR IGNORE INTO capacidades (capacidade_ml) VALUES (50)",
        "INSERT OR IGNORE INTO capacidades (capacidade_ml) VALUES (100)",
        "INSERT OR IGNORE INTO capacidades (capacidade_ml) VALUES (250)",
        "INSERT OR IGNORE INTO capacidades (capacidade_ml) VALUES (500)",
        "INSERT OR IGNORE INTO capacidades (capacidade_ml) VALUES (1000)"
    ]
    
    for sql in dados_iniciais:
        executar_sql(sql, show_error=False)

def testar_conexao():
    """Testa a conexão com o banco de dados"""
    try:
        # Verificar se o arquivo do banco existe
        if os.path.exists(DB_PATH):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cursor.fetchall()
            conn.close()
            
            if tabelas:
                return True, f"✅ Conexão estabelecida! {len(tabelas)} tabelas encontradas."
            else:
                return True, "✅ Banco de dados conectado (sem tabelas ainda)."
        else:
            return True, "✅ SQLite pronto para criar banco de dados."
    except Exception as e:
        return False, f"❌ Erro de conexão: {str(e)}"

# Menu lateral simplificado
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3208/3208720.png", width=100)
    st.markdown("## 🖨️ Sistema de Cartuchos")
    st.markdown(f"**Banco de dados:** `{DB_PATH}`")
    
    # Mostrar tamanho do arquivo do banco
    if os.path.exists(DB_PATH):
        tamanho_kb = os.path.getsize(DB_PATH) / 1024
        st.caption(f"Tamanho: {tamanho_kb:.1f} KB")
    
    st.divider()
    
    # Menu manual usando radio buttons
    menu_options = ["📊 Dashboard", "📝 Cadastros", "🔍 Consultas", "⚙️ Configurações", "🗄️ SQL Executor"]
    
    # Criar botões de menu manualmente
    selected = st.radio(
        "Menu Principal",
        options=menu_options,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Botões de ação
    if st.button("🔗 Testar Conexão", use_container_width=True):
        sucesso, mensagem = testar_conexao()
        if sucesso:
            st.success(mensagem)
        else:
            st.error(mensagem)
    
    if st.button("🔄 Inicializar Banco", use_container_width=True, type="primary"):
        with st.spinner("Criando tabelas..."):
            resultados = criar_tabelas()
            for resultado in resultados:
                st.write(resultado)
        
        with st.spinner("Inserindo dados iniciais..."):
            inserir_dados_iniciais()
            st.success("✅ Dados iniciais inseridos!")

# ===== PÁGINA: DASHBOARD =====
if selected == "📊 Dashboard":
    st.markdown("<h1 class='main-header'>📊 Dashboard - Sistema de Cartuchos</h1>", unsafe_allow_html=True)
    
    # Testar conexão primeiro
    sucesso, mensagem = testar_conexao()
    if not sucesso:
        st.error(mensagem)
    
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
    
    # Criar tabs usando st.tabs (nativo do Streamlit)
    tab_titles = ["🖨️ Fabricantes", "🖨️ Modelos", "🎨 Cores", "📦 Capacidades", "🖨️ Cartuchos"]
    tabs = st.tabs(tab_titles)
    
    # TAB 1: Fabricantes
    with tabs[0]:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<h3 class='sub-header'>Cadastrar Novo</h3>", unsafe_allow_html=True)
            
            with st.form("form_fabricante", clear_on_submit=True):
                nome_fabricante = st.text_input("Nome do Fabricante", placeholder="Ex: Epson, HP, Canon")
                submitted = st.form_submit_button("✅ Cadastrar Fabricante")
                
                if submitted and nome_fabricante:
                    query = "INSERT INTO fabricantes (nome) VALUES (?)"
                    resultado = executar_sql(query, params=(nome_fabricante,))
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
            query = "SELECT id, nome, strftime('%d/%m/%Y %H:%M', data_criacao) as data_criacao FROM fabricantes ORDER BY nome"
            fabricantes_df = executar_sql(query, fetch=True)
            
            if fabricantes_df is not None and not fabricantes_df.empty:
                st.dataframe(fabricantes_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum fabricante cadastrado.")
    
    # TAB 2: Modelos de Impressora
    with tabs[1]:
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
                        query = "INSERT INTO modelos_impressora (nome, fabricante_id) VALUES (?, ?)"
                        if executar_sql(query, params=(nome_modelo, fabricante_id)):
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
                SELECT mi.id, mi.nome, f.nome as fabricante, 
                       strftime('%d/%m/%Y %H:%M', mi.data_criacao) as data_criacao
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
    with tabs[2]:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<h3 class='sub-header'>Cadastrar Nova Cor</h3>", unsafe_allow_html=True)
            
            with st.form("form_cor", clear_on_submit=True):
                nome_cor = st.text_input("Nome da Cor", placeholder="Ex: Black, Cyan, Magenta")
                codigo_hex = st.color_picker("Código Hex", "#000000")
                submitted = st.form_submit_button("✅ Cadastrar Cor")
                
                if submitted and nome_cor:
                    query = "INSERT INTO cores_referencia (nome, codigo_hex) VALUES (?, ?)"
                    if executar_sql(query, params=(nome_cor, codigo_hex)):
                        st.success(f"✅ Cor '{nome_cor}' cadastrada com sucesso!")
                        st.markdown(f"""
                        <div class='sql-box'>
                            SQL Executado:<br>
                            INSERT INTO cores_referencia (nome, codigo_hex) VALUES ('{nome_cor}', '{codigo_hex}')
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3 class='sub-header'>Cores Cadastradas</h3>", unsafe_allow_html=True)
            query = "SELECT id, nome, codigo_hex, strftime('%d/%m/%Y %H:%M', data_criacao) as data_criacao FROM cores_referencia ORDER BY nome"
            cores_df = executar_sql(query, fetch=True)
            
            if cores_df is not None and not cores_df.empty:
                st.dataframe(cores_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma cor cadastrada.")
    
    # TAB 4: Capacidades
    with tabs[3]:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("<h3 class='sub-header'>Cadastrar Nova Capacidade</h3>", unsafe_allow_html=True)
            
            with st.form("form_capacidade", clear_on_submit=True):
                capacidade_ml = st.number_input("Capacidade (ml)", min_value=1, step=1, value=100)
                submitted = st.form_submit_button("✅ Cadastrar Capacidade")
                
                if submitted:
                    query = "INSERT INTO capacidades (capacidade_ml) VALUES (?)"
                    if executar_sql(query, params=(int(capacidade_ml),)):
                        st.success(f"✅ Capacidade de {capacidade_ml}ml cadastrada com sucesso!")
                        st.markdown(f"""
                        <div class='sql-box'>
                            SQL Executado:<br>
                            INSERT INTO capacidades (capacidade_ml) VALUES ({capacidade_ml})
                        </div>
                        """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3 class='sub-header'>Capacidades Cadastradas</h3>", unsafe_allow_html=True)
            query = "SELECT id, capacidade_ml, strftime('%d/%m/%Y %H:%M', data_criacao) as data_criacao FROM capacidades ORDER BY capacidade_ml"
            capacidades_df = executar_sql(query, fetch=True)
            
            if capacidades_df is not None and not capacidades_df.empty:
                st.dataframe(capacidades_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma capacidade cadastrada.")
    
    # TAB 5: Cartuchos
    with tabs[4]:
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
                        VALUES (?, ?, ?, ?)
                    """
                    
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        # Inserir cartucho e obter o ID
                        cursor.execute(query_cartucho, (modelo_cartucho, cor_id, modelo_id, codigo_referencia))
                        cartucho_id = cursor.lastrowid
                        conn.commit()
                        
                        # Associar capacidades
                        for cap_str in capacidades_selecionadas:
                            capacidade_ml = int(cap_str.replace("ml", ""))
                            capacidade_id = int(capacidades_df[capacidades_df['capacidade_ml'] == capacidade_ml].iloc[0]['id'])
                            query_associar = """
                                INSERT INTO cartucho_capacidades (cartucho_id, capacidade_id)
                                VALUES (?, ?)
                            """
                            cursor.execute(query_associar, (cartucho_id, capacidade_id))
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
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
                GROUP_CONCAT(cap.capacidade_ml) as capacidades,
                strftime('%d/%m/%Y %H:%M', c.data_criacao) as data_criacao
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
                GROUP_CONCAT(cap.capacidade_ml) as capacidades
            FROM cartuchos c
            JOIN cores_referencia cr ON c.cor_id = cr.id
            JOIN modelos_impressora mi ON c.modelo_impressora_id = mi.id
            JOIN fabricantes f ON mi.fabricante_id = f.id
            LEFT JOIN cartucho_capacidades cc ON c.id = cc.cartucho_id
            LEFT JOIN capacidades cap ON cc.capacidade_id = cap.id
            WHERE 1=1
        """
        
        params = []
        
        if filtro_cor != "Todos":
            query_base += " AND cr.nome = ?"
            params.append(filtro_cor)
        
        if filtro_fabricante != "Todos":
            query_base += " AND f.nome = ?"
            params.append(filtro_fabricante)
        
        if filtro_capacidade != "Todas":
            capacidade_ml = int(filtro_capacidade.replace("ml", ""))
            query_base += " AND cap.capacidade_ml = ?"
            params.append(capacidade_ml)
        
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
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tabelas = cursor.fetchall()
        
        if tabelas:
            for (tabela,) in tabelas:
                with st.expander(f"📁 {tabela}"):
                    # Obter estrutura da tabela
                    cursor.execute(f"PRAGMA table_info({tabela})")
                    colunas_info = cursor.fetchall()
                    
                    # Converter para DataFrame
                    colunas_df = pd.DataFrame(colunas_info, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
                    st.dataframe(colunas_df[['name', 'type', 'notnull', 'pk']].rename(
                        columns={'name': 'Coluna', 'type': 'Tipo', 'notnull': 'Obrigatório', 'pk': 'Chave Primária'}
                    ), hide_index=True)
                    
                    # Mostrar dados de exemplo
                    dados_exemplo = executar_sql(f"SELECT * FROM {tabela} LIMIT 5", fetch=True)
                    if dados_exemplo is not None and not dados_exemplo.empty:
                        st.write(f"**Dados de exemplo (5 primeiros registros):**")
                        st.dataframe(dados_exemplo, hide_index=True)
        else:
            st.info("Nenhuma tabela encontrada no banco de dados.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"❌ Erro ao listar estrutura: {str(e)}")

# ===== PÁGINA: CONFIGURAÇÕES =====
elif selected == "⚙️ Configurações":
    st.markdown("<h1 class='main-header'>⚙️ Configurações do Sistema</h1>", unsafe_allow_html=True)
    
    # Configuração de conexão
    st.markdown("### 🔧 Configuração de Conexão")
    
    with st.expander("Informações do SQLite"):
        st.info(f"""
        **Banco de dados:** {DB_PATH}
        
        SQLite é um banco de dados embutido que armazena tudo em um único arquivo.
        
        **Vantagens:**
        - Não precisa de servidor separado
        - Arquivo único fácil de fazer backup
        - Leve e rápido
        - Ideal para aplicações pequenas/médias
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Gerar Backup SQL", use_container_width=True):
            # Gerar script SQL de backup
            backup_sql = f"-- Backup do Sistema de Cartuchos\n-- Banco: {DB_PATH}\n-- Data: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Listar tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tabelas = cursor.fetchall()
                
                for (tabela,) in tabelas:
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
                
                cursor.close()
                conn.close()
                
                # Mostrar e permitir download
                st.download_button(
                    label="📥 Download Backup.sql",
                    data=backup_sql,
                    file_name=f"backup_cartuchos_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.sql",
                    mime="text/plain"
                )
                
                with st.expander("📝 Visualizar Backup"):
                    st.code(backup_sql, language="sql")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar backup: {str(e)}")
    
    with col2:
        if st.button("🗑️ Limpar Banco de Dados", use_container_width=True, type="secondary"):
            st.warning("⚠️ Esta ação irá apagar todos os dados!")
            confirmar = st.checkbox("Confirmar que deseja apagar todos os dados")
            
            if confirmar and st.button("✅ Confirmar Exclusão", type="primary"):
                try:
                    # Fechar conexões
                    conn = get_connection()
                    conn.close()
                    
                    # Remover arquivo do banco
                    if os.path.exists(DB_PATH):
                        os.remove(DB_PATH)
                        st.success("✅ Banco de dados excluído com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao excluir banco: {str(e)}")
    
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
    🖨️ Sistema de Gerenciamento de Cartuchos | Desenvolvido com Streamlit + SQLite
</div>
""", unsafe_allow_html=True)
