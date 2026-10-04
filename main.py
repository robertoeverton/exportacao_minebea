import io
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Setup Exportação - Indaía Comex",
    page_icon="✈️",
    layout="wide"  # <--- Isso faz a página ocupar toda a largura da tela!
)

try:
    st.image("banner.png", use_container_width=True)
except Exception:
    st.warning("Imagem de banner não encontrada.")

# ==========================================
# 1. TELA DE LOGIN SEGURA
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔒 Acesso Restrito - Form de Exportação")
        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", type="primary")

            if submit:
                # Lendo as credenciais de forma segura através do st.secrets
                try:
                    user_correto = st.secrets["credenciais"]["usuario"]
                    senha_correta = st.secrets["credenciais"]["senha"]
                except KeyError:
                    st.error("Erro interno: Credenciais não configuradas no servidor.")
                    return

                if usuario == user_correto and senha == senha_correta:
                    st.session_state["logged_in"] = True
                    st.success("Login efetuado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")

if not st.session_state["logged_in"]:
    login()
    st.stop()

# Botão de Logout na Barra Lateral
with st.sidebar:
    st.write(f"👤 Logado como: **{st.secrets['credenciais']['usuario']}**")
    if st.button("Sair (Logout)"):
        st.session_state["logged_in"] = False
        st.rerun()

# ==========================================
# APLICAÇÃO PRINCIPAL (Sem alterações na sua lógica de negócio excelente)
# ==========================================
st.subheader("Formulário de Setup Exportação ✈️🚢🚚📦")

st.markdown("---")
# 1. Upload do Arquivo FORA do formulário para disparar a leitura dos dados
st.subheader("1. Importação da Nota Fiscal")
nf_upload = st.file_uploader("Faça o upload do XML da Nota Fiscal", type=["xml"])

st.markdown("---")
# Variáveis padrão
num_nf = 0
cliente_nome = ""
endereco_cliente = ""  # Endereço do destinatário
itens_nf = []
colunas = [
    "PN",
    "Descrição",
    "Descrição em Inglês",
    "PO Cliente / PN",
    "QTD",
    "Peso Unitário (kg)",
    "Valor Unitário",
    "NCM",
]

# Lógica de extração do XML
if nf_upload is not None:
    try:
        tree = ET.parse(nf_upload)
        root = tree.getroot()

        # O XML da NFe possui namespaces que precisam ser mapeados
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
        infNFe = root.find(".//nfe:infNFe", ns)

        if infNFe is not None:
            # Extração do Número da NF
            elem_nnf = infNFe.find(".//nfe:ide/nfe:nNF", ns)
            if elem_nnf is not None:
                num_nf = int(elem_nnf.text)

            # Extração de Dados do Destinatário (Cliente) e seu Endereço
            elem_dest_nome = infNFe.find(".//nfe:dest/nfe:xNome", ns)
            if elem_dest_nome is not None:
                cliente_nome = elem_dest_nome.text

            elem_dest_ender = infNFe.find(".//nfe:dest/nfe:enderDest", ns)
            if elem_dest_ender is not None:
                lgr = (
                    elem_dest_ender.find("nfe:xLgr", ns).text
                    if elem_dest_ender.find("nfe:xLgr", ns) is not None
                    else ""
                )
                nro = (
                    elem_dest_ender.find("nfe:nro", ns).text
                    if elem_dest_ender.find("nfe:nro", ns) is not None
                    else ""
                )
                bairro = (
                    elem_dest_ender.find("nfe:xBairro", ns).text
                    if elem_dest_ender.find("nfe:xBairro", ns) is not None
                    else ""
                )
                pais = (
                    elem_dest_ender.find("nfe:xPais", ns).text
                    if elem_dest_ender.find("nfe:xPais", ns) is not None
                    else ""
                )

                # Montando o endereço do cliente
                endereco_cliente = f"{lgr}, {nro} - {bairro} - {pais}"

            # Extração de Itens da Grade
            for det in infNFe.findall(".//nfe:det", ns):
                prod = det.find("nfe:prod", ns)
                if prod is not None:
                    pn = (
                        prod.find("nfe:cProd", ns).text
                        if prod.find("nfe:cProd", ns) is not None
                        else ""
                    )
                    desc = (
                        prod.find("nfe:xProd", ns).text
                        if prod.find("nfe:xProd", ns) is not None
                        else ""
                    )
                    qtd = (
                        float(prod.find("nfe:qCom", ns).text)
                        if prod.find("nfe:qCom", ns) is not None
                        else 0.0
                    )
                    vun = (
                        float(prod.find("nfe:vUnCom", ns).text)
                        if prod.find("nfe:vUnCom", ns) is not None
                        else 0.0
                    )
                    ncm = (
                        prod.find("nfe:NCM", ns).text
                        if prod.find("nfe:NCM", ns) is not None
                        else ""
                    )

                    itens_nf.append({
                        "PN": pn,
                        "Descrição": desc,
                        "Descrição em Inglês": "",
                        "PO Cliente / PN": "",
                        "QTD": qtd,
                        "Peso Unitário (kg)": 0.0,
                        "Valor Unitário": vun,
                        "NCM": ncm,
                    })
        st.success(
            "XML processado com sucesso! Os campos abaixo foram preenchidos."
        )
    except Exception as e:
        st.error(f"Erro ao ler o XML: {e}")

# Transforma a lista de itens num DataFrame
if len(itens_nf) > 0:
    df_dados = pd.DataFrame(itens_nf)
else:
    df_dados = pd.DataFrame(columns=colunas)

# 2. Criação do Formulário
st.subheader("2. Informações Gerais da Exportação")
col1, col2, col3, col4, col5 = st.columns(5)

ref_mine = col1.text_input(
    "1. Referência MINE", placeholder="EXPMINEXXXX/XX", max_chars=14
)
nf = col2.number_input("2. Número NF", format="%d", step=1, value=num_nf)
cliente = col3.text_input("3. Nome do Cliente / Invoice To", value=cliente_nome)
end_cliente = col4.text_input("4. Endereço do Cliente", value=endereco_cliente)
pais_destino = col5.text_input("5. País Destino")

st.markdown("---")

col6, col7, col8, col9, col10 = st.columns(5)

entrega_igual = col6.radio(
    "6. Destino Final é o Mesmo do Importador?",
    ["SIM", "NÃO"],
    key="entrega_igual",
    captions=[
        "O local de entrega será no mesmo endereço do Importador",
        "O local de entrega será diferente do endereço do Importador",
    ],
)

if st.session_state.entrega_igual == "NÃO":
    final_empresa = col7.text_input("7. Razão Social / Nome Importador Final")
    final_empresa_endereco = col8.text_input("8. Endereço Importador Final")
    final_empresa_pais = col9.text_input("9. País Importador Final")
    final_empresa_contato = col10.text_input(
        "10. Contato / E-mail / Telefone Final"
    )
else:
    final_empresa, final_empresa_endereco, final_empresa_pais, (
        final_empresa_contato
    ) = ("N/A (Mesmo do Importador)", "", "", "")

st.markdown("---")
col11, col12, col13, col14, col15 = st.columns(5)
incoterm = col11.selectbox(
    "11. Incoterm", ["", "FOB", "CIF", "EXW", "DDP", "FCA", "CFR"], help=""" 
                    FOB - Nós entregamos a carga limpa e desembaraçada a bordo do navio/veículo indicado pelo comprador.
                    CIF - Nós pagamos o frete principal e o seguro até o porto/aeroporto de destino.
                    EXW - O comprador retira a mercadoria em nossa fábrica e assume todos os custos e riscos.
                    DDP - Nós entregamos a mercadoria diretamente no seu endereço, com todas as taxas, impostos e frete totalmente pagos.
                    FCA - Nós entregamos a mercadoria ao transportador que o comprador contratar.
                    CFR - Nós (vendedores) pagamos o frete internacional até o porto de destino escolhido pelo comprador."""
)
moeda = col12.selectbox("12. Moeda da Operação", ["", "USD - DOLAR", "EUR - EURO"])
modal = col13.selectbox(
    "13. Modal de Embarque", ["", "AEREO", "MARITIMO", "RODOVIARIO"]
)
local_embarque = col14.selectbox(
    "14. Porto / Aeroporto Embarque", ["", "SANTOS", "GUARUJA", "GRU", "VCP"]
)
agente_transportadora = col15.text_input(
    "15. Contato Agente de Carga/Transportadora"
)

st.markdown("---")
col16, col17, col18, col19, col20 = st.columns(5)

qtd_volume = col16.number_input(
    "16. Quantidade de Volume", min_value=0, max_value=500, step=1, value=1
)
especie = col17.selectbox("17. Espécie dos Volumes", ["", "BOX", "PALLET"])
dimensoes = col18.text_input(
    "18. Dimensões do Volume", placeholder="10 x 10 x 10 CM"
)
cond_pgto = col19.selectbox(
    "19. Condição de Pagamento",
    [
        "",
        "Antecipado",
        "À Vista",
        "30 Dias",
        "60 Dias",
        "90 Dias",
        "Sem Cobertura Cambial",
    ],
)
local_entrega = col20.text_input("20. Local de Entrega da Mercadoria")

st.markdown("---")
data_embarque = st.date_input("Data Prevista para Embarque")
st.markdown("---")

st.subheader("3. Grade de Itens")
st.caption(
    "Traduza a descrição preenchendo a coluna 'Descrição em Inglês'. Você"
    " também pode adicionar itens ou ajustar os pesos."
)

df_editado = st.data_editor(
    df_dados, num_rows="dynamic", use_container_width=True, key="grid_itens"
)

st.markdown("---")

# ==========================================
# FUNÇÃO PARA GERAR ARQUIVO EXCEL
# ==========================================
def gerar_excel(dados_gerais, df_itens):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Aba 1: Informações Gerais
        df_info = pd.DataFrame(
            list(dados_gerais.items()), columns=["Campo / Parâmetro", "Valor"]
        )
        df_info.to_excel(writer, sheet_name="Informações Gerais", index=False)

        # Aba 2: Grade de Itens
        df_itens.to_excel(writer, sheet_name="Itens da Exportação", index=False)

    output.seek(0)
    return output

# ==========================================
# 2 & 3. VALIDAÇÃO E GERAÇÃO DO ARQUIVO EXCEL
# ==========================================
if st.button("Registrar e Gerar Excel de Exportação", type="primary"):
    erros = []

    # Validação Coluna por Coluna (1 a 20)
    if not ref_mine.strip():
        erros.append("Campo 1: Referência MINE está em branco.")
    if nf <= 0:
        erros.append("Campo 2: Número da NF deve ser maior que zero.")
    if not cliente.strip():
        erros.append("Campo 3: Nome do Cliente / Invoice To está em branco.")
    if not end_cliente.strip():
        erros.append("Campo 4: Endereço do Cliente está em branco.")
    if not pais_destino.strip():
        erros.append("Campo 5: País Destino está em branco.")

    if entrega_igual == "NÃO":
        if not final_empresa.strip():
            erros.append(
                "Campo 7: Razão Social/Nome do Importador Final está em branco."
            )
        if not final_empresa_endereco.strip():
            erros.append("Campo 8: Endereço do Importador Final está em branco.")
        if not final_empresa_pais.strip():
            erros.append("Campo 9: País do Importador Final está em branco.")
        if not final_empresa_contato.strip():
            erros.append(
                "Campo 10: Contato/E-mail/Telefone do Importador Final está em"
                " branco."
            )

    if not incoterm:
        erros.append("Campo 11: Selecione um Incoterm.")
    if not moeda:
        erros.append("Campo 12: Selecione a Moeda da Operação.")
    if not modal:
        erros.append("Campo 13: Selecione o Modal de Embarque.")
    if not local_embarque:
        erros.append("Campo 14: Selecione o Porto/Aeroporto de Embarque.")
    if not agente_transportadora.strip():
        erros.append("Campo 15: Contato Agente/Transportadora está em branco.")

    if qtd_volume <= 0:
        erros.append("Campo 16: Quantidade de Volume deve ser pelo menos 1.")
    if not especie:
        erros.append("Campo 17: Selecione a Espécie dos Volumes.")
    if not dimensoes.strip():
        erros.append("Campo 18: Dimensões do Volume está em branco.")
    if not cond_pgto:
        erros.append("Campo 19: Selecione a Condição de Pagamento.")
    if not local_entrega.strip():
        erros.append("Campo 20: Local de Entrega da Mercadoria está em branco.")

    # Validação da Tabela de Itens
    if df_editado.empty:
        erros.append("A Grade de Itens não pode estar vazia.")
    else:
        for col in df_editado.columns:
            # Verifica se há células vazias ou com valor 0 em campos numéricos chave
            tem_vazios = df_editado[col].astype(str).str.strip().eq("").any()
            if tem_vazios:
                erros.append(
                    f"A coluna '{col}' da Grade de Itens possui campos em branco."
                )

    # Exibição do Resultado
    if erros:
        st.error(
            "❌ **Não foi possível gerar o arquivo! Preencha todos os campos"
            " obrigatórios:**"
        )
        for err in erros:
            st.write(f"- {err}")
    else:
        st.success(
            "✅ **Todos os campos foram validados com sucesso! Clique abaixo para"
            " baixar o arquivo Excel.**"
        )

        # Dicionário com os dados validados
        dados_exportacao = {
            "Referência MINE": ref_mine,
            "Número NF": nf,
            "Nome do Cliente": cliente,
            "Endereço do Cliente": end_cliente,
            "País Destino": pais_destino,
            "Entrega em endereço diferente?": entrega_igual,
            "Importador Final": final_empresa,
            "Endereço Importador Final": final_empresa_endereco,
            "País Importador Final": final_empresa_pais,
            "Contato Importador Final": final_empresa_contato,
            "Incoterm": incoterm,
            "Moeda": moeda,
            "Modal": modal,
            "Local de Embarque": local_embarque,
            "Agente de Carga/Transportadora": agente_transportadora,
            "Qtd Volumes": qtd_volume,
            "Espécie Volumes": especie,
            "Dimensões": dimensoes,
            "Condição de Pagamento": cond_pgto,
            "Local de Entrega": local_entrega,
            "Data Prevista Embarque": str(data_embarque),
        }

        # Gera o arquivo Excel em memória
        excel_file = gerar_excel(dados_exportacao, df_editado)

        # Botão para Download do Excel
        st.download_button(
            label="📥 Baixar Solicitação de Invoice (.xlsx)",
            data=excel_file,
            file_name=f"Solicitacao_Invoice_NF_{nf}_{ref_mine.replace('/', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

footer_html = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #0e1117;
    color: #FAFAFA;
    text-align: center;
    padding: 10px;
    font-size: 14px;
    font-family: sans-serif;
    border-top: 1px solid #31333F;
    z-index: 999;
}
.footer b {
    color: #FF4B4B;
}
</style>
<div class="footer">
    <p>Developed & Maintained by <b>Everton Roberto</b> | Indaía Comex Team</p>
</div>
"""
# Exibe o rodapé fixo
st.markdown(footer_html, unsafe_allow_html=True)
