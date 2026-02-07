"""
Sistema de Controle de Estoque com QR Code - CAMDA
"""

import streamlit as st
import qrcode
import json
import pandas as pd
from io import BytesIO
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageFont
import base64

# Configuração
st.set_page_config(
    page_title="📦 Controle de Estoque - QR Code",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1a5276;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #2ecc71;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #1a5276, #2980b9);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-card h2 { margin: 0; font-size: 2rem; }
    .stat-card p { margin: 0; font-size: 0.9rem; opacity: 0.85; }
    .success-box {
        background: #d5f5e3;
        border-left: 4px solid #2ecc71;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .error-box {
        background: #fadbd8;
        border-left: 4px solid #e74c3c;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: #fef9e7;
        border-left: 4px solid #f39c12;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO DA SESSÃO
# ============================================================
if "produtos" not in st.session_state:
    st.session_state.produtos = [
        {"id": "ENGEO20", "nome": "Inseticida Engeo Pleno S", "volume": "20L", "categoria": "Inseticida"},
        {"id": "ACTARA5", "nome": "Inseticida Actara 750 SG", "volume": "5kg", "categoria": "Inseticida"},
        {"id": "FRONDEO5", "nome": "Inseticida Frondeo", "volume": "5L", "categoria": "Inseticida"},
        {"id": "SPERTO5", "nome": "Inseticida Sperto", "volume": "5kg", "categoria": "Inseticida"},
        {"id": "PRIORI20", "nome": "Fungicida Priori Xtra", "volume": "20L", "categoria": "Fungicida"},
        {"id": "REVERB5", "nome": "Fungicida Microbiológico Reverb", "volume": "5L", "categoria": "Fungicida"},
        {"id": "ROUNDUP20", "nome": "Herbicida Roundup Transorb R", "volume": "20L", "categoria": "Herbicida"},
        {"id": "GLIFO20", "nome": "Herbicida Glifosato 72 WG Alamos", "volume": "20kg", "categoria": "Herbicida"},
        {"id": "AGEFIX20", "nome": "Óleo Mineral Agefix E8", "volume": "20L", "categoria": "Adjuvante"},
        {"id": "ALTACOR5", "nome": "Inseticida Altacor", "volume": "5kg", "categoria": "Inseticida"},
        {"id": "METOMIL20", "nome": "Inseticida Metomil 215 SL", "volume": "20L", "categoria": "Inseticida"},
    ]

if "unidades" not in st.session_state:
    st.session_state.unidades = []
if "proximo_numero" not in st.session_state:
    st.session_state.proximo_numero = 1
if "pedidos" not in st.session_state:
    st.session_state.pedidos = []
if "leituras" not in st.session_state:
    st.session_state.leituras = []

# ============================================================
# FUNÇÕES
# ============================================================
def gerar_qr_code(dados, tamanho_box=15, border=4):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=tamanho_box,
        border=border,
    )
    qr.add_data(json.dumps(dados, ensure_ascii=False))
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def gerar_etiqueta(unidade, produto, largura=1200, altura=1500):
    img = Image.new("RGB", (largura, altura), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_titulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_info = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_numero = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_pequena = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except OSError:
        font_titulo = ImageFont.load_default()
        font_info = font_titulo
        font_numero = font_titulo
        font_pequena = font_titulo

    # Borda
    draw.rectangle([10, 10, largura - 10, altura - 10], outline="black", width=4)

    # Cabeçalho
    draw.rectangle([10, 10, largura - 10, 100], fill="#1a5276")
    draw.text((largura // 2, 55), "CAMDA - CONTROLE DE ESTOQUE",
              fill="white", font=font_titulo, anchor="mm")

    # Número grande
    numero_str = f"#{unidade['numero']:04d}"
    draw.text((largura // 2, 170), numero_str,
              fill="#e74c3c", font=font_numero, anchor="mm")

    # QR Code
    dados_qr = {
        "n": unidade["numero"],
        "p": produto["id"],
        "nome": produto["nome"],
        "vol": produto["volume"],
        "val": unidade["validade"],
        "lote": unidade.get("lote", ""),
        "dt": unidade["data_cadastro"]
    }
    qr_img = gerar_qr_code(dados_qr, tamanho_box=12)
    qr_tamanho = 650
    qr_img = qr_img.resize((qr_tamanho, qr_tamanho))
    qr_x = (largura - qr_tamanho) // 2
    qr_y = 230
    img.paste(qr_img, (qr_x, qr_y))

    # Informações
    y_info = qr_y + qr_tamanho + 30
    info_lines = [
        f"Produto: {produto['nome']}",
        f"Volume: {produto['volume']}",
        f"Categoria: {produto['categoria']}",
        f"Validade: {unidade['validade']}",
        f"Lote: {unidade.get('lote', 'N/I')}",
        f"Cadastro: {unidade['data_cadastro']}",
    ]
    for line in info_lines:
        draw.text((largura // 2, y_info), line,
                  fill="black", font=font_info, anchor="mm")
        y_info += 50

    # Rodapé
    draw.rectangle([10, altura - 60, largura - 10, altura - 10], fill="#2ecc71")
    draw.text((largura // 2, altura - 35), f"Código: {produto['id']} | Unidade: {numero_str}",
              fill="white", font=font_pequena, anchor="mm")

    return img


def imagem_para_bytes(img, formato="PNG"):
    buffer = BytesIO()
    img.save(buffer, format=formato)
    return buffer.getvalue()


def gerar_pdf_etiquetas(unidades_selecionadas):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4

    for i, un in enumerate(unidades_selecionadas):
        produto = next((p for p in st.session_state.produtos if p["id"] == un["produto_id"]), None)
        if not produto:
            continue

        etiqueta = gerar_etiqueta(un, produto)
        img_buffer = BytesIO()
        etiqueta.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)

        margin = 40
        available_w = page_w - 2 * margin
        available_h = page_h - 2 * margin
        img_w, img_h = etiqueta.size
        ratio = min(available_w / img_w, available_h / img_h)
        draw_w = img_w * ratio
        draw_h = img_h * ratio
        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2
        c.drawImage(img_reader, x, y, draw_w, draw_h)

        if i < len(unidades_selecionadas) - 1:
            c.showPage()

    c.save()
    return buffer.getvalue()


def buscar_produto_por_id(produto_id):
    return next((p for p in st.session_state.produtos if p["id"] == produto_id), None)


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("## 📦 Menu")
pagina = st.sidebar.radio(
    "Navegação",
    ["🏠 Painel Geral", "📋 Cadastro de Produtos", "🏷️ Cadastrar Unidades",
     "🖨️ Gerar Etiquetas", "📷 Leitor de QR Code", "🚚 Verificar Pedido",
     "📊 Relatórios"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Resumo Rápido")
st.sidebar.metric("Tipos de Produto", len(st.session_state.produtos))
st.sidebar.metric("Unidades Cadastradas", len(st.session_state.unidades))
st.sidebar.metric("Próximo Número", f"#{st.session_state.proximo_numero:04d}")

hoje = date.today()
vencidos = 0
proximos_vencer = 0
for un in st.session_state.unidades:
    try:
        val = datetime.strptime(un["validade"], "%d/%m/%Y").date()
        if val < hoje:
            vencidos += 1
        elif (val - hoje).days <= 30:
            proximos_vencer += 1
    except (ValueError, KeyError):
        pass

if vencidos > 0:
    st.sidebar.error(f"⚠️ {vencidos} unidade(s) VENCIDA(s)!")
if proximos_vencer > 0:
    st.sidebar.warning(f"⏰ {proximos_vencer} vencem em até 30 dias")


# ============================================================
# PAINEL GERAL
# ============================================================
if pagina == "🏠 Painel Geral":
    st.markdown('<div class="main-header">📦 Controle de Estoque com QR Code</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><h2>{len(st.session_state.produtos)}</h2><p>Tipos de Produto</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><h2>{len(st.session_state.unidades)}</h2><p>Unidades no Estoque</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><h2>{vencidos}</h2><p>Unidades Vencidas</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-card"><h2>{proximos_vencer}</h2><p>Vencem em 30 dias</p></div>', unsafe_allow_html=True)

    st.markdown("### 📋 Últimas Unidades Cadastradas")
    if st.session_state.unidades:
        ultimas = st.session_state.unidades[-10:][::-1]
        df = pd.DataFrame(ultimas)
        df["produto"] = df["produto_id"].apply(
            lambda x: buscar_produto_por_id(x)["nome"] if buscar_produto_por_id(x) else "?"
        )
        df = df[["numero", "produto", "validade", "lote", "data_cadastro"]]
        df.columns = ["Nº", "Produto", "Validade", "Lote", "Cadastro"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma unidade cadastrada ainda. Vá em **🏷️ Cadastrar Unidades** para começar.")

    st.markdown("### 📦 Estoque por Produto")
    if st.session_state.unidades:
        contagem = {}
        for un in st.session_state.unidades:
            prod = buscar_produto_por_id(un["produto_id"])
            nome = prod["nome"] if prod else "Desconhecido"
            contagem[nome] = contagem.get(nome, 0) + 1
        df_estoque = pd.DataFrame(list(contagem.items()), columns=["Produto", "Quantidade"])
        df_estoque = df_estoque.sort_values("Quantidade", ascending=False)
        st.bar_chart(df_estoque.set_index("Produto"))


# ============================================================
# CADASTRO DE PRODUTOS
# ============================================================
elif pagina == "📋 Cadastro de Produtos":
    st.markdown('<div class="main-header">📋 Cadastro de Tipos de Produto</div>', unsafe_allow_html=True)

    st.markdown("### Produtos Cadastrados")
    if st.session_state.produtos:
        df_prod = pd.DataFrame(st.session_state.produtos)
        df_prod.columns = ["Código", "Nome", "Volume", "Categoria"]
        st.dataframe(df_prod, use_container_width=True, hide_index=True)

    st.markdown("### ➕ Adicionar Novo Produto")
    with st.form("form_produto"):
        col1, col2 = st.columns(2)
        with col1:
            novo_id = st.text_input("Código (ex: PRIORI20)", max_chars=20)
            novo_nome = st.text_input("Nome do Produto")
        with col2:
            novo_volume = st.text_input("Volume/Peso (ex: 20L, 5kg)")
            nova_cat = st.selectbox("Categoria",
                                    ["Inseticida", "Fungicida", "Herbicida", "Adjuvante",
                                     "Acaricida", "Fertilizante", "Outro"])

        if st.form_submit_button("✅ Adicionar Produto", use_container_width=True):
            if novo_id and novo_nome and novo_volume:
                if any(p["id"] == novo_id.upper() for p in st.session_state.produtos):
                    st.error("Código já existe!")
                else:
                    st.session_state.produtos.append({
                        "id": novo_id.upper(),
                        "nome": novo_nome,
                        "volume": novo_volume,
                        "categoria": nova_cat
                    })
                    st.success(f"Produto **{novo_nome}** adicionado!")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos.")

    st.markdown("### 📤 Importar de Planilha")
    uploaded = st.file_uploader("Envie CSV ou Excel com colunas: id, nome, volume, categoria",
                                type=["csv", "xlsx"])
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df_imp = pd.read_csv(uploaded)
            else:
                df_imp = pd.read_excel(uploaded)
            st.dataframe(df_imp.head(), use_container_width=True)
            if st.button("✅ Importar Produtos"):
                count = 0
                for _, row in df_imp.iterrows():
                    pid = str(row.get("id", "")).upper().strip()
                    if pid and not any(p["id"] == pid for p in st.session_state.produtos):
                        st.session_state.produtos.append({
                            "id": pid,
                            "nome": str(row.get("nome", "")),
                            "volume": str(row.get("volume", "")),
                            "categoria": str(row.get("categoria", "Outro"))
                        })
                        count += 1
                st.success(f"{count} produtos importados!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")


# ============================================================
# CADASTRAR UNIDADES
# ============================================================
elif pagina == "🏷️ Cadastrar Unidades":
    st.markdown('<div class="main-header">🏷️ Cadastrar Unidades Individuais</div>', unsafe_allow_html=True)

    st.info(f"Próximo número disponível: **#{st.session_state.proximo_numero:04d}**")

    with st.form("form_unidade"):
        col1, col2 = st.columns(2)
        with col1:
            produto_nomes = [f"{p['id']} - {p['nome']} {p['volume']}" for p in st.session_state.produtos]
            produto_sel = st.selectbox("Produto", produto_nomes)
            quantidade = st.number_input("Quantidade de unidades a cadastrar", min_value=1, max_value=100, value=1)
        with col2:
            validade = st.date_input("Data de Validade")
            lote = st.text_input("Lote (opcional)", placeholder="Ex: 2025-A")

        if st.form_submit_button("🏷️ Cadastrar Unidade(s)", use_container_width=True):
            produto_id = produto_sel.split(" - ")[0]
            novas_unidades = []
            for i in range(quantidade):
                unidade = {
                    "numero": st.session_state.proximo_numero,
                    "produto_id": produto_id,
                    "validade": validade.strftime("%d/%m/%Y"),
                    "lote": lote if lote else "N/I",
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "status": "em_estoque"
                }
                st.session_state.unidades.append(unidade)
                novas_unidades.append(unidade)
                st.session_state.proximo_numero += 1

            prod = buscar_produto_por_id(produto_id)
            st.success(f"✅ {quantidade} unidade(s) de **{prod['nome']}** cadastrada(s)! "
                       f"(#{novas_unidades[0]['numero']:04d} a #{novas_unidades[-1]['numero']:04d})")

            st.markdown("### 👀 Preview das Etiquetas")
            cols = st.columns(min(quantidade, 3))
            for i, un in enumerate(novas_unidades[:3]):
                with cols[i % 3]:
                    etiqueta = gerar_etiqueta(un, prod)
                    st.image(etiqueta, caption=f"Unidade #{un['numero']:04d}", width=300)

    st.markdown("### 📋 Unidades Cadastradas")
    if st.session_state.unidades:
        df_un = pd.DataFrame(st.session_state.unidades)
        df_un["produto"] = df_un["produto_id"].apply(
            lambda x: buscar_produto_por_id(x)["nome"] if buscar_produto_por_id(x) else "?"
        )
        st.dataframe(
            df_un[["numero", "produto", "validade", "lote", "data_cadastro", "status"]].rename(
                columns={"numero": "Nº", "produto": "Produto", "validade": "Validade",
                          "lote": "Lote", "data_cadastro": "Cadastro", "status": "Status"}
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# GERAR ETIQUETAS
# ============================================================
elif pagina == "🖨️ Gerar Etiquetas":
    st.markdown('<div class="main-header">🖨️ Gerar Etiquetas para Impressão</div>', unsafe_allow_html=True)

    if not st.session_state.unidades:
        st.warning("Nenhuma unidade cadastrada. Cadastre unidades primeiro.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            filtro_produto = st.selectbox(
                "Filtrar por produto",
                ["Todos"] + [f"{p['id']} - {p['nome']}" for p in st.session_state.produtos]
            )
        with col2:
            filtro_status = st.selectbox("Filtrar por status", ["Todos", "em_estoque", "expedido"])

        unidades_filtradas = st.session_state.unidades.copy()
        if filtro_produto != "Todos":
            pid = filtro_produto.split(" - ")[0]
            unidades_filtradas = [u for u in unidades_filtradas if u["produto_id"] == pid]
        if filtro_status != "Todos":
            unidades_filtradas = [u for u in unidades_filtradas if u.get("status") == filtro_status]

        st.info(f"**{len(unidades_filtradas)}** unidades encontradas")

        if unidades_filtradas:
            numeros = [u["numero"] for u in unidades_filtradas]
            col1, col2 = st.columns(2)
            with col1:
                num_de = st.number_input("Do número", min_value=min(numeros), max_value=max(numeros), value=min(numeros))
            with col2:
                num_ate = st.number_input("Até número", min_value=min(numeros), max_value=max(numeros), value=max(numeros))

            selecionadas = [u for u in unidades_filtradas if num_de <= u["numero"] <= num_ate]
            st.write(f"**{len(selecionadas)}** etiquetas serão geradas")

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("👁️ Visualizar Etiquetas", use_container_width=True):
                    for un in selecionadas[:6]:
                        prod = buscar_produto_por_id(un["produto_id"])
                        if prod:
                            etiqueta = gerar_etiqueta(un, prod)
                            st.image(etiqueta, caption=f"Unidade #{un['numero']:04d} - {prod['nome']}", width=350)

            with col_btn2:
                if st.button("📄 Gerar PDF para Impressão", use_container_width=True):
                    with st.spinner("Gerando PDF..."):
                        try:
                            pdf_bytes = gerar_pdf_etiquetas(selecionadas)
                            st.download_button(
                                label="⬇️ Baixar PDF",
                                data=pdf_bytes,
                                file_name=f"etiquetas_{num_de}_a_{num_ate}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Erro ao gerar PDF: {e}")
                            for un in selecionadas:
                                prod = buscar_produto_por_id(un["produto_id"])
                                if prod:
                                    etiqueta = gerar_etiqueta(un, prod)
                                    img_bytes = imagem_para_bytes(etiqueta)
                                    st.download_button(
                                        f"⬇️ Etiqueta #{un['numero']:04d}",
                                        img_bytes,
                                        f"etiqueta_{un['numero']:04d}.png",
                                        "image/png"
                                    )


# ============================================================
# LEITOR DE QR CODE
# ============================================================
elif pagina == "📷 Leitor de QR Code":
    st.markdown('<div class="main-header">📷 Leitor de QR Code</div>', unsafe_allow_html=True)

    st.markdown("""
    ### Como usar:
    1. **Upload:** Tire uma foto do QR code e faça upload
    2. **Câmera:** Use a câmera do navegador
    3. **Manual:** Cole o conteúdo JSON do QR code
    """)

    tab1, tab2, tab3 = st.tabs(["📸 Upload de Foto", "📹 Câmera", "⌨️ Manual"])

    with tab1:
        foto = st.file_uploader("Envie uma foto do QR Code", type=["png", "jpg", "jpeg", "webp"])
        if foto:
            img = Image.open(foto)
            st.image(img, width=400)
            try:
                from pyzbar.pyzbar import decode
                resultados = decode(img)
                if resultados:
                    for r in resultados:
                        dados = json.loads(r.data.decode())
                        st.markdown(f'<div class="success-box"><b>✅ QR Code Lido!</b></div>', unsafe_allow_html=True)
                        st.json(dados)
                        st.session_state.leituras.append({
                            "numero": dados.get("n"),
                            "produto_id": dados.get("p"),
                            "nome": dados.get("nome"),
                            "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        })
                else:
                    st.warning("Nenhum QR code encontrado na imagem.")
            except ImportError:
                st.warning("pyzbar não disponível.")

    with tab2:
        camera_foto = st.camera_input("Aponte para o QR Code")
        if camera_foto:
            img = Image.open(camera_foto)
            try:
                from pyzbar.pyzbar import decode
                resultados = decode(img)
                if resultados:
                    for r in resultados:
                        dados = json.loads(r.data.decode())
                        st.success("✅ QR Code Lido!")
                        st.json(dados)
                        st.session_state.leituras.append({
                            "numero": dados.get("n"),
                            "produto_id": dados.get("p"),
                            "nome": dados.get("nome"),
                            "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        })
                else:
                    st.warning("QR code não detectado. Tente com melhor foco/iluminação.")
            except ImportError:
                st.warning("pyzbar não disponível.")

    with tab3:
        texto_qr = st.text_area("Cole o conteúdo JSON do QR Code")
        if st.button("Processar") and texto_qr:
            try:
                dados = json.loads(texto_qr)
                st.success("✅ Dados processados!")
                st.json(dados)
                st.session_state.leituras.append({
                    "numero": dados.get("n"),
                    "produto_id": dados.get("p"),
                    "nome": dados.get("nome"),
                    "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                })
            except json.JSONDecodeError:
                st.error("JSON inválido.")

    if st.session_state.leituras:
        st.markdown("### 📜 Histórico de Leituras")
        df_leit = pd.DataFrame(st.session_state.leituras)
        st.dataframe(df_leit, use_container_width=True, hide_index=True)
        if st.button("🗑️ Limpar leituras"):
            st.session_state.leituras = []
            st.rerun()


# ============================================================
# VERIFICAR PEDIDO
# ============================================================
elif pagina == "🚚 Verificar Pedido":
    st.markdown('<div class="main-header">🚚 Verificação de Carregamento</div>', unsafe_allow_html=True)

    st.markdown("### 📝 Montar Pedido")
    with st.form("form_pedido"):
        cliente = st.text_input("Nome do Cliente")
        st.markdown("**Itens do Pedido:**")
        itens = []
        for i in range(5):
            col1, col2 = st.columns([3, 1])
            with col1:
                prod = st.selectbox(
                    f"Produto {i + 1}",
                    ["(nenhum)"] + [f"{p['id']} - {p['nome']} {p['volume']}" for p in st.session_state.produtos],
                    key=f"ped_prod_{i}"
                )
            with col2:
                qtd = st.number_input(f"Qtd", min_value=0, max_value=500, value=0, key=f"ped_qtd_{i}")
            if prod != "(nenhum)" and qtd > 0:
                itens.append({"produto_id": prod.split(" - ")[0], "quantidade": qtd})

        if st.form_submit_button("✅ Salvar Pedido", use_container_width=True):
            if cliente and itens:
                pedido = {
                    "cliente": cliente,
                    "itens": itens,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "status": "pendente"
                }
                st.session_state.pedidos.append(pedido)
                st.success(f"Pedido de **{cliente}** salvo com {len(itens)} item(ns)!")
                st.rerun()
            else:
                st.warning("Preencha o cliente e adicione pelo menos 1 item.")

    st.markdown("### 🔍 Verificar Carregamento")
    if st.session_state.pedidos:
        pedidos_pendentes = [p for p in st.session_state.pedidos if p["status"] == "pendente"]
        if pedidos_pendentes:
            pedido_sel = st.selectbox(
                "Selecione o pedido",
                [f"{p['cliente']} - {p['data']}" for p in pedidos_pendentes]
            )
            idx = [f"{p['cliente']} - {p['data']}" for p in pedidos_pendentes].index(pedido_sel)
            pedido = pedidos_pendentes[idx]

            st.markdown("**Itens esperados:**")
            for item in pedido["itens"]:
                prod = buscar_produto_por_id(item["produto_id"])
                if prod:
                    st.write(f"- {prod['nome']} {prod['volume']} × {item['quantidade']}")

            st.markdown("**Produtos escaneados:**")
            if st.session_state.leituras:
                lidos = {}
                for leitura in st.session_state.leituras:
                    pid = leitura.get("produto_id", "")
                    lidos[pid] = lidos.get(pid, 0) + 1

                tudo_ok = True
                for item in pedido["itens"]:
                    esperado = item["quantidade"]
                    lido = lidos.get(item["produto_id"], 0)
                    prod = buscar_produto_por_id(item["produto_id"])
                    nome = prod["nome"] if prod else item["produto_id"]

                    if lido == esperado:
                        st.markdown(f'<div class="success-box">✅ {nome}: {lido}/{esperado} — OK</div>', unsafe_allow_html=True)
                    elif lido < esperado:
                        st.markdown(f'<div class="warning-box">⏳ {nome}: {lido}/{esperado} — Faltam {esperado - lido}</div>', unsafe_allow_html=True)
                        tudo_ok = False
                    else:
                        st.markdown(f'<div class="error-box">❌ {nome}: {lido}/{esperado} — {lido - esperado} a mais!</div>', unsafe_allow_html=True)
                        tudo_ok = False

                for pid, qtd in lidos.items():
                    if not any(item["produto_id"] == pid for item in pedido["itens"]):
                        prod = buscar_produto_por_id(pid)
                        nome = prod["nome"] if prod else pid
                        st.markdown(f'<div class="error-box">🚫 {nome}: {qtd} un. — NÃO ESTÁ NO PEDIDO!</div>', unsafe_allow_html=True)
                        tudo_ok = False

                if tudo_ok:
                    st.balloons()
                    st.success("🎉 Carregamento 100% correto!")
            else:
                st.info("Nenhum produto escaneado. Vá em **📷 Leitor de QR Code** para escanear.")
    else:
        st.info("Nenhum pedido cadastrado.")


# ============================================================
# RELATÓRIOS
# ============================================================
elif pagina == "📊 Relatórios":
    st.markdown('<div class="main-header">📊 Relatórios</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📦 Estoque Atual", "⏰ Validades", "📤 Exportar"])

    with tab1:
        if st.session_state.unidades:
            contagem = {}
            for un in st.session_state.unidades:
                prod = buscar_produto_por_id(un["produto_id"])
                if prod:
                    chave = f"{prod['nome']} {prod['volume']}"
                    if chave not in contagem:
                        contagem[chave] = {"Produto": prod["nome"], "Volume": prod["volume"],
                                           "Categoria": prod["categoria"], "Quantidade": 0}
                    contagem[chave]["Quantidade"] += 1
            df_est = pd.DataFrame(contagem.values()).sort_values("Quantidade", ascending=False)
            st.dataframe(df_est, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma unidade cadastrada.")

    with tab2:
        if st.session_state.unidades:
            registros = []
            for un in st.session_state.unidades:
                prod = buscar_produto_por_id(un["produto_id"])
                try:
                    val = datetime.strptime(un["validade"], "%d/%m/%Y").date()
                    dias = (val - hoje).days
                    if dias < 0:
                        status_val = "🔴 VENCIDO"
                    elif dias <= 30:
                        status_val = "🟡 Vence em breve"
                    elif dias <= 90:
                        status_val = "🟠 Atenção"
                    else:
                        status_val = "🟢 OK"
                except (ValueError, KeyError):
                    dias = None
                    status_val = "❓ Sem data"
                registros.append({
                    "Nº": un["numero"],
                    "Produto": prod["nome"] if prod else "?",
                    "Validade": un["validade"],
                    "Dias Restantes": dias if dias is not None else "N/A",
                    "Status": status_val
                })
            df_val = pd.DataFrame(registros).sort_values("Dias Restantes")
            st.dataframe(df_val, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma unidade cadastrada.")

    with tab3:
        if st.session_state.unidades:
            df_export = pd.DataFrame(st.session_state.unidades)
            df_export["produto_nome"] = df_export["produto_id"].apply(
                lambda x: buscar_produto_por_id(x)["nome"] if buscar_produto_por_id(x) else "?"
            )
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exportar Estoque (CSV)", csv_data, "estoque_completo.csv", "text/csv",
                               use_container_width=True)

            dados_json = json.dumps({
                "produtos": st.session_state.produtos,
                "unidades": st.session_state.unidades,
                "pedidos": st.session_state.pedidos,
                "proximo_numero": st.session_state.proximo_numero
            }, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button("⬇️ Backup Completo (JSON)", dados_json, "backup_estoque.json",
                               "application/json", use_container_width=True)

        st.markdown("### 📥 Importar Backup")
        backup_file = st.file_uploader("Carregar JSON de backup", type=["json"])
        if backup_file:
            try:
                dados = json.loads(backup_file.read())
                if st.button("✅ Restaurar Backup"):
                    st.session_state.produtos = dados.get("produtos", [])
                    st.session_state.unidades = dados.get("unidades", [])
                    st.session_state.pedidos = dados.get("pedidos", [])
                    st.session_state.proximo_numero = dados.get("proximo_numero", 1)
                    st.success("Backup restaurado!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
