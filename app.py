from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    json,
    send_from_directory

)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import json


app = Flask(__name__)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

DATA_DIR = os.environ.get(
    "DATA_DIR",
    os.path.join(BASE_DIR, "data")
)

UPLOAD_FOLDER = os.path.join(
    DATA_DIR,
    "uploads"
)

DATABASE_PATH = os.path.join(
    DATA_DIR,
    "delivery.db"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "nunes-delivery-chave-local"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{DATABASE_PATH.replace(os.sep, '/')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

db = SQLAlchemy(app)


# =========================================================
# MODELOS
# =========================================================

class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    ativa = db.Column(
        db.Boolean,
        default=True
    )

    ordem = db.Column(
        db.Integer,
        default=0
    )

    produtos = db.relationship(
        "Produto",
        backref="categoria",
        lazy=True
    )


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    descricao = db.Column(
        db.Text,
        nullable=True
    )

    preco = db.Column(
        db.Float,
        nullable=False
    )

    imagem = db.Column(
        db.String(255),
        nullable=True
    )

    emoji = db.Column(
        db.String(20),
        default="🍔"
    )

    disponivel = db.Column(
        db.Boolean,
        default=True
    )

    destaque = db.Column(
        db.Boolean,
        default=False
    )

    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id"),
        nullable=False
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Configuracao(db.Model):
    __tablename__ = "configuracoes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome_loja = db.Column(
        db.String(150),
        default="Nunes Delivery"
    )

    descricao = db.Column(
        db.String(255),
        default="Seu pedido, rápido e fácil."
    )

    telefone = db.Column(
        db.String(30),
        nullable=True
    )

    chave_pix = db.Column(
        db.String(255),
        nullable=True
    )

    taxa_entrega = db.Column(
        db.Float,
        default=5.00
    )

    pedido_minimo = db.Column(
        db.Float,
        default=0.00
    )

    loja_aberta = db.Column(
        db.Boolean,
        default=True
    )


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome_cliente = db.Column(
        db.String(150),
        nullable=False
    )

    telefone = db.Column(
        db.String(30),
        nullable=False
    )

    cep = db.Column(
        db.String(15),
        nullable=True
    )

    rua = db.Column(
        db.String(180),
        nullable=False
    )

    numero = db.Column(
        db.String(30),
        nullable=False
    )

    bairro = db.Column(
        db.String(100),
        nullable=False
    )

    complemento = db.Column(
        db.String(150),
        nullable=True
    )

    referencia = db.Column(
        db.String(200),
        nullable=True
    )

    observacao = db.Column(
        db.Text,
        nullable=True
    )

    forma_pagamento = db.Column(
        db.String(30),
        default="PIX"
    )

    subtotal = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    taxa_entrega = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(40),
        default="Recebido"
    )

    criado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    itens = db.relationship(
        "PedidoItem",
        backref="pedido",
        lazy=True,
        cascade="all, delete-orphan"
    )


class PedidoItem(db.Model):
    __tablename__ = "pedido_itens"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id"),
        nullable=False
    )

    produto_id = db.Column(
        db.Integer,
        nullable=False
    )

    nome_produto = db.Column(
        db.String(150),
        nullable=False
    )

    preco_unitario = db.Column(
        db.Float,
        nullable=False
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False
    )

    total_item = db.Column(
        db.Float,
        nullable=False
    )




@app.route("/uploads/<path:nome_arquivo>")
def arquivo_upload(nome_arquivo):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        nome_arquivo
    )
# =========================================================
# CONFIGURAÇÕES
# =========================================================

@app.route(
    "/admin/configuracoes",
    methods=["GET", "POST"]
)
def admin_configuracoes():
    configuracao = Configuracao.query.first()

    if not configuracao:
        configuracao = Configuracao(
            nome_loja="Nunes Delivery",
            descricao="Seu pedido, rápido e fácil.",
            taxa_entrega=0,
            pedido_minimo=0,
            loja_aberta=True
        )

        db.session.add(configuracao)
        db.session.commit()

    if request.method == "POST":
        nome_loja = request.form.get(
            "nome_loja",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        telefone = request.form.get(
            "telefone",
            ""
        ).strip()

        chave_pix = request.form.get(
            "chave_pix",
            ""
        ).strip()

        taxa_entrega_form = request.form.get(
            "taxa_entrega",
            "0"
        ).strip()

        pedido_minimo_form = request.form.get(
            "pedido_minimo",
            "0"
        ).strip()

        loja_aberta = (
            request.form.get("loja_aberta")
            == "on"
        )

        if not nome_loja:
            flash(
                "Digite o nome da loja.",
                "erro"
            )

            return redirect(
                url_for("admin_configuracoes")
            )

        try:
            taxa_entrega = converter_preco(
                taxa_entrega_form
            )

            pedido_minimo = converter_preco(
                pedido_minimo_form
            )

            if taxa_entrega < 0:
                taxa_entrega = 0

            if pedido_minimo < 0:
                pedido_minimo = 0

        except ValueError:
            flash(
                "Digite valores válidos para taxa e pedido mínimo.",
                "erro"
            )

            return redirect(
                url_for("admin_configuracoes")
            )

        configuracao.nome_loja = nome_loja
        configuracao.descricao = descricao
        configuracao.telefone = telefone
        configuracao.chave_pix = chave_pix
        configuracao.taxa_entrega = taxa_entrega
        configuracao.pedido_minimo = pedido_minimo
        configuracao.loja_aberta = loja_aberta

        db.session.commit()

        flash(
            "Configurações atualizadas com sucesso.",
            "sucesso"
        )

        return redirect(
            url_for("admin_configuracoes")
        )

    return render_template(
        "admin/configuracoes.html",
        configuracao=configuracao
    )    
# =========================================================
# PEDIDOS
# =========================================================

@app.route("/admin/pedidos")
def admin_pedidos():
    status_filtro = request.args.get(
        "status",
        ""
    ).strip()

    busca = request.args.get(
        "busca",
        ""
    ).strip()

    consulta = Pedido.query

    if status_filtro:
        consulta = consulta.filter(
            Pedido.status == status_filtro
        )

    if busca:
        filtros_busca = [
            Pedido.nome_cliente.ilike(
                f"%{busca}%"
            ),
            Pedido.telefone.ilike(
                f"%{busca}%"
            )
        ]

        if busca.isdigit():
            filtros_busca.append(
                Pedido.id == int(busca)
            )

        consulta = consulta.filter(
            db.or_(*filtros_busca)
        )

    pedidos = consulta.order_by(
        Pedido.criado_em.desc()
    ).all()

    status_disponiveis = [
        "Recebido",
        "Em preparo",
        "Saiu para entrega",
        "Entregue",
        "Cancelado"
    ]

    return render_template(
        "admin/pedidos.html",
        pedidos=pedidos,
        busca=busca,
        status_filtro=status_filtro,
        status_disponiveis=status_disponiveis
    )


@app.route(
    "/admin/pedidos/<int:pedido_id>"
)
def admin_detalhe_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    status_disponiveis = [
        "Recebido",
        "Em preparo",
        "Saiu para entrega",
        "Entregue",
        "Cancelado"
    ]

    return render_template(
        "admin/pedido_detalhe.html",
        pedido=pedido,
        status_disponiveis=status_disponiveis
    )


@app.route(
    "/admin/pedidos/<int:pedido_id>/status",
    methods=["POST"]
)
def atualizar_status_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    novo_status = request.form.get(
        "status",
        ""
    ).strip()

    status_permitidos = [
        "Recebido",
        "Em preparo",
        "Saiu para entrega",
        "Entregue",
        "Cancelado"
    ]

    if novo_status not in status_permitidos:
        flash(
            "Status inválido.",
            "erro"
        )

        return redirect(
            url_for(
                "admin_detalhe_pedido",
                pedido_id=pedido.id
            )
        )

    pedido.status = novo_status

    db.session.commit()

    flash(
        f"Pedido #{pedido.id} atualizado para "
        f"{novo_status}.",
        "sucesso"
    )

    pagina_retorno = request.form.get(
        "pagina_retorno",
        "detalhe"
    )

    if pagina_retorno == "lista":
        return redirect(
            url_for("admin_pedidos")
        )

    return redirect(
        url_for(
            "admin_detalhe_pedido",
            pedido_id=pedido.id
        )
    )
# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def extensao_permitida(nome_arquivo):
    return (
        "." in nome_arquivo
        and nome_arquivo.rsplit(".", 1)[1].lower()
        in EXTENSOES_PERMITIDAS
    )


def salvar_imagem(arquivo):
    if not arquivo or arquivo.filename == "":
        return None

    if not extensao_permitida(arquivo.filename):
        return None

    nome_seguro = secure_filename(arquivo.filename)

    extensao = nome_seguro.rsplit(".", 1)[1].lower()

    nome_novo = f"{uuid.uuid4().hex}.{extensao}"

    caminho = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nome_novo
    )

    arquivo.save(caminho)

    return nome_novo


def excluir_imagem(nome_imagem):
    if not nome_imagem:
        return

    caminho = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nome_imagem
    )

    if os.path.exists(caminho):
        try:
            os.remove(caminho)
        except OSError:
            pass


def converter_preco(valor):
    if not valor:
        return 0.0

    valor = valor.strip()

    if "," in valor:
        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")

    return float(valor)


# =========================================================
# ROTAS DO CARDÁPIO
# =========================================================

@app.route("/")
def cardapio():
    categorias = Categoria.query.filter_by(
        ativa=True
    ).order_by(
        Categoria.ordem,
        Categoria.nome
    ).all()

    produtos = (
        Produto.query
        .join(Categoria)
        .filter(
            Produto.disponivel.is_(True),
            Categoria.ativa.is_(True)
        )
        .order_by(
            Produto.destaque.desc(),
            Produto.nome
        )
        .all()
    )

    configuracao = Configuracao.query.first()

    return render_template(
        "cardapio.html",
        categorias=categorias,
        produtos=produtos,
        configuracao=configuracao
    )

# =========================================================
# CHECKOUT
# =========================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
def checkout():
    configuracao = Configuracao.query.first()

    if request.method == "POST":
        nome_cliente = request.form.get(
            "nome_cliente",
            ""
        ).strip()

        telefone = request.form.get(
            "telefone",
            ""
        ).strip()

        cep = request.form.get(
            "cep",
            ""
        ).strip()

        rua = request.form.get(
            "rua",
            ""
        ).strip()

        numero = request.form.get(
            "numero",
            ""
        ).strip()

        bairro = request.form.get(
            "bairro",
            ""
        ).strip()

        complemento = request.form.get(
            "complemento",
            ""
        ).strip()

        referencia = request.form.get(
            "referencia",
            ""
        ).strip()

        observacao = request.form.get(
            "observacao",
            ""
        ).strip()

        carrinho_json = request.form.get(
            "carrinho_json",
            ""
        ).strip()

        if not nome_cliente:
            flash(
                "Digite o nome do cliente.",
                "erro"
            )

            return redirect(
                url_for("checkout")
            )

        if not telefone:
            flash(
                "Digite o telefone.",
                "erro"
            )

            return redirect(
                url_for("checkout")
            )

        if not rua or not numero or not bairro:
            flash(
                "Preencha rua, número e bairro.",
                "erro"
            )

            return redirect(
                url_for("checkout")
            )

        if not carrinho_json:
            flash(
                "O carrinho está vazio.",
                "erro"
            )

            return redirect(
                url_for("cardapio")
            )

        try:
            carrinho_recebido = json.loads(
                carrinho_json
            )
        except json.JSONDecodeError:
            flash(
                "Não foi possível carregar o carrinho.",
                "erro"
            )

            return redirect(
                url_for("cardapio")
            )

        if not isinstance(carrinho_recebido, list):
            flash(
                "Carrinho inválido.",
                "erro"
            )

            return redirect(
                url_for("cardapio")
            )

        itens_validos = []
        subtotal = 0.0

        for item in carrinho_recebido:
            try:
                produto_id = int(
                    item.get("id")
                )

                quantidade = int(
                    item.get("quantidade", 0)
                )
            except (
                TypeError,
                ValueError,
                AttributeError
            ):
                continue

            if quantidade <= 0:
                continue

            produto = Produto.query.filter_by(
                id=produto_id,
                disponivel=True
            ).first()

            if not produto:
                continue

            total_item = (
                produto.preco * quantidade
            )

            subtotal += total_item

            itens_validos.append({
                "produto": produto,
                "quantidade": quantidade,
                "total_item": total_item
            })

        if not itens_validos:
            flash(
                "Nenhum produto válido foi encontrado.",
                "erro"
            )

            return redirect(
                url_for("cardapio")
            )

        taxa_entrega = float(
            configuracao.taxa_entrega or 0
        )

        total = subtotal + taxa_entrega

        pedido_minimo = float(
            configuracao.pedido_minimo or 0
        )

        if (
            pedido_minimo > 0
            and subtotal < pedido_minimo
        ):
            flash(
                "O pedido mínimo é de "
                f"R$ {pedido_minimo:.2f}"
                .replace(".", ","),
                "erro"
            )

            return redirect(
                url_for("checkout")
            )

        pedido = Pedido(
            nome_cliente=nome_cliente,
            telefone=telefone,
            cep=cep,
            rua=rua,
            numero=numero,
            bairro=bairro,
            complemento=complemento,
            referencia=referencia,
            observacao=observacao,
            forma_pagamento="PIX",
            subtotal=subtotal,
            taxa_entrega=taxa_entrega,
            total=total,
            status="Recebido"
        )

        db.session.add(pedido)
        db.session.flush()

        for item in itens_validos:
            produto = item["produto"]
            quantidade = item["quantidade"]
            total_item = item["total_item"]

            pedido_item = PedidoItem(
                pedido_id=pedido.id,
                produto_id=produto.id,
                nome_produto=produto.nome,
                preco_unitario=produto.preco,
                quantidade=quantidade,
                total_item=total_item
            )

            db.session.add(pedido_item)

        db.session.commit()

        return redirect(
            url_for(
                "pedido_confirmado",
                pedido_id=pedido.id
            )
        )

    return render_template(
        "checkout.html",
        configuracao=configuracao
    )   

@app.route("/pedido/<int:pedido_id>")
def pedido_confirmado(pedido_id):
    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    configuracao = Configuracao.query.first()

    return render_template(
        "pedido_confirmado.html",
        pedido=pedido,
        configuracao=configuracao
    )     

@app.route(
    "/api/pedidos/<int:pedido_id>/status"
)
def api_status_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    return jsonify({
        "id": pedido.id,
        "status": pedido.status,
        "atualizado": datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    })
# =========================================================
# DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():
    total_produtos = Produto.query.count()
    total_categorias = Categoria.query.count()

    produtos_disponiveis = Produto.query.filter_by(
        disponivel=True
    ).count()

    total_pedidos = Pedido.query.count()

    pedidos_recebidos = Pedido.query.filter_by(
        status="Recebido"
    ).count()

    pedidos_preparo = Pedido.query.filter_by(
        status="Em preparo"
    ).count()

    pedidos_entregues = Pedido.query.filter_by(
        status="Entregue"
    ).count()

    pedidos_recentes = Pedido.query.order_by(
        Pedido.criado_em.desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_produtos=total_produtos,
        total_categorias=total_categorias,
        produtos_disponiveis=produtos_disponiveis,
        total_pedidos=total_pedidos,
        pedidos_recebidos=pedidos_recebidos,
        pedidos_preparo=pedidos_preparo,
        pedidos_entregues=pedidos_entregues,
        pedidos_recentes=pedidos_recentes
    )

# =========================================================
# CATEGORIAS
# =========================================================

@app.route(
    "/admin/categorias",
    methods=["GET", "POST"]
)
def admin_categorias():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        ordem = request.form.get("ordem", "0").strip()
        ativa = request.form.get("ativa") == "on"

        if not nome:
            flash(
                "Digite o nome da categoria.",
                "erro"
            )

            return redirect(
                url_for("admin_categorias")
            )

        try:
            ordem = int(ordem)
        except ValueError:
            ordem = 0

        categoria_existente = Categoria.query.filter(
            db.func.lower(Categoria.nome)
            == nome.lower()
        ).first()

        if categoria_existente:
            flash(
                "Já existe uma categoria com esse nome.",
                "erro"
            )

            return redirect(
                url_for("admin_categorias")
            )

        categoria = Categoria(
            nome=nome,
            ordem=ordem,
            ativa=ativa
        )

        db.session.add(categoria)
        db.session.commit()

        flash(
            "Categoria cadastrada com sucesso.",
            "sucesso"
        )

        return redirect(
            url_for("admin_categorias")
        )

    categorias = Categoria.query.order_by(
        Categoria.ordem,
        Categoria.nome
    ).all()

    return render_template(
        "admin/categorias.html",
        categorias=categorias
    )


@app.route(
    "/admin/categorias/<int:categoria_id>/editar",
    methods=["GET", "POST"]
)
def editar_categoria(categoria_id):
    categoria = Categoria.query.get_or_404(
        categoria_id
    )

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        ordem = request.form.get("ordem", "0").strip()
        ativa = request.form.get("ativa") == "on"

        if not nome:
            flash(
                "Digite o nome da categoria.",
                "erro"
            )

            return redirect(
                url_for(
                    "editar_categoria",
                    categoria_id=categoria.id
                )
            )

        try:
            ordem = int(ordem)
        except ValueError:
            ordem = 0

        categoria_existente = Categoria.query.filter(
            db.func.lower(Categoria.nome)
            == nome.lower(),
            Categoria.id != categoria.id
        ).first()

        if categoria_existente:
            flash(
                "Já existe outra categoria com esse nome.",
                "erro"
            )

            return redirect(
                url_for(
                    "editar_categoria",
                    categoria_id=categoria.id
                )
            )

        categoria.nome = nome
        categoria.ordem = ordem
        categoria.ativa = ativa

        db.session.commit()

        flash(
            "Categoria atualizada com sucesso.",
            "sucesso"
        )

        return redirect(
            url_for("admin_categorias")
        )

    return render_template(
        "admin/categoria_form.html",
        categoria=categoria
    )


@app.route(
    "/admin/categorias/<int:categoria_id>/status",
    methods=["POST"]
)
def alterar_status_categoria(categoria_id):
    categoria = Categoria.query.get_or_404(
        categoria_id
    )

    categoria.ativa = not categoria.ativa

    db.session.commit()

    flash(
        "Status da categoria atualizado.",
        "sucesso"
    )

    return redirect(
        url_for("admin_categorias")
    )


@app.route(
    "/admin/categorias/<int:categoria_id>/excluir",
    methods=["POST"]
)
def excluir_categoria(categoria_id):
    categoria = Categoria.query.get_or_404(
        categoria_id
    )

    if categoria.produtos:
        flash(
            "Não é possível excluir uma categoria "
            "que possui produtos.",
            "erro"
        )

        return redirect(
            url_for("admin_categorias")
        )

    db.session.delete(categoria)
    db.session.commit()

    flash(
        "Categoria excluída com sucesso.",
        "sucesso"
    )

    return redirect(
        url_for("admin_categorias")
    )


# =========================================================
# PRODUTOS
# =========================================================

@app.route("/admin/produtos")
def admin_produtos():
    busca = request.args.get(
        "busca",
        ""
    ).strip()

    categoria_id = request.args.get(
        "categoria",
        ""
    ).strip()

    consulta = Produto.query

    if busca:
        consulta = consulta.filter(
            Produto.nome.ilike(f"%{busca}%")
        )

    if categoria_id.isdigit():
        consulta = consulta.filter_by(
            categoria_id=int(categoria_id)
        )

    produtos = consulta.order_by(
        Produto.criado_em.desc()
    ).all()

    categorias = Categoria.query.order_by(
        Categoria.nome
    ).all()

    return render_template(
        "admin/produtos.html",
        produtos=produtos,
        categorias=categorias,
        busca=busca,
        categoria_selecionada=categoria_id
    )


@app.route(
    "/admin/produtos/novo",
    methods=["GET", "POST"]
)
def novo_produto():
    categorias = Categoria.query.order_by(
        Categoria.nome
    ).all()

    if request.method == "POST":
        nome = request.form.get(
            "nome",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        preco_formulario = request.form.get(
            "preco",
            ""
        ).strip()

        emoji = request.form.get(
            "emoji",
            "🍔"
        ).strip() or "🍔"

        categoria_id = request.form.get(
            "categoria_id",
            ""
        ).strip()

        disponivel = (
            request.form.get("disponivel")
            == "on"
        )

        destaque = (
            request.form.get("destaque")
            == "on"
        )

        if not nome:
            flash(
                "Digite o nome do produto.",
                "erro"
            )

            return render_template(
                "admin/produto_form.html",
                categorias=categorias,
                produto=None
            )

        try:
            preco = converter_preco(
                preco_formulario
            )

            if preco <= 0:
                raise ValueError

        except ValueError:
            flash(
                "Digite um preço válido.",
                "erro"
            )

            return render_template(
                "admin/produto_form.html",
                categorias=categorias,
                produto=None
            )

        if not categoria_id.isdigit():
            flash(
                "Selecione uma categoria.",
                "erro"
            )

            return render_template(
                "admin/produto_form.html",
                categorias=categorias,
                produto=None
            )

        categoria = Categoria.query.get(
            int(categoria_id)
        )

        if not categoria:
            flash(
                "Categoria inválida.",
                "erro"
            )

            return render_template(
                "admin/produto_form.html",
                categorias=categorias,
                produto=None
            )

        arquivo = request.files.get("imagem")
        nome_imagem = None

        if arquivo and arquivo.filename:
            if not extensao_permitida(
                arquivo.filename
            ):
                flash(
                    "Imagem inválida. Use PNG, JPG, "
                    "JPEG ou WEBP.",
                    "erro"
                )

                return render_template(
                    "admin/produto_form.html",
                    categorias=categorias,
                    produto=None
                )

            nome_imagem = salvar_imagem(arquivo)

        produto = Produto(
            nome=nome,
            descricao=descricao,
            preco=preco,
            imagem=nome_imagem,
            emoji=emoji,
            categoria_id=categoria.id,
            disponivel=disponivel,
            destaque=destaque
        )

        db.session.add(produto)
        db.session.commit()

        flash(
            "Produto cadastrado com sucesso.",
            "sucesso"
        )

        return redirect(
            url_for("admin_produtos")
        )

    return render_template(
        "admin/produto_form.html",
        categorias=categorias,
        produto=None
    )


@app.route(
    "/admin/produtos/<int:produto_id>/editar",
    methods=["GET", "POST"]
)
def editar_produto(produto_id):
    produto = Produto.query.get_or_404(
        produto_id
    )

    categorias = Categoria.query.order_by(
        Categoria.nome
    ).all()

    if request.method == "POST":
        nome = request.form.get(
            "nome",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        preco_formulario = request.form.get(
            "preco",
            ""
        ).strip()

        emoji = request.form.get(
            "emoji",
            "🍔"
        ).strip() or "🍔"

        categoria_id = request.form.get(
            "categoria_id",
            ""
        ).strip()

        disponivel = (
            request.form.get("disponivel")
            == "on"
        )

        destaque = (
            request.form.get("destaque")
            == "on"
        )

        remover_imagem = (
            request.form.get("remover_imagem")
            == "on"
        )

        if not nome:
            flash(
                "Digite o nome do produto.",
                "erro"
            )

            return redirect(
                url_for(
                    "editar_produto",
                    produto_id=produto.id
                )
            )

        try:
            preco = converter_preco(
                preco_formulario
            )

            if preco <= 0:
                raise ValueError

        except ValueError:
            flash(
                "Digite um preço válido.",
                "erro"
            )

            return redirect(
                url_for(
                    "editar_produto",
                    produto_id=produto.id
                )
            )

        if not categoria_id.isdigit():
            flash(
                "Selecione uma categoria.",
                "erro"
            )

            return redirect(
                url_for(
                    "editar_produto",
                    produto_id=produto.id
                )
            )

        categoria = Categoria.query.get(
            int(categoria_id)
        )

        if not categoria:
            flash(
                "Categoria inválida.",
                "erro"
            )

            return redirect(
                url_for(
                    "editar_produto",
                    produto_id=produto.id
                )
            )

        arquivo = request.files.get("imagem")

        if remover_imagem and produto.imagem:
            excluir_imagem(produto.imagem)
            produto.imagem = None

        if arquivo and arquivo.filename:
            if not extensao_permitida(
                arquivo.filename
            ):
                flash(
                    "Imagem inválida. Use PNG, JPG, "
                    "JPEG ou WEBP.",
                    "erro"
                )

                return redirect(
                    url_for(
                        "editar_produto",
                        produto_id=produto.id
                    )
                )

            nova_imagem = salvar_imagem(arquivo)

            if nova_imagem:
                excluir_imagem(produto.imagem)
                produto.imagem = nova_imagem

        produto.nome = nome
        produto.descricao = descricao
        produto.preco = preco
        produto.emoji = emoji
        produto.categoria_id = categoria.id
        produto.disponivel = disponivel
        produto.destaque = destaque

        db.session.commit()

        flash(
            "Produto atualizado com sucesso.",
            "sucesso"
        )

        return redirect(
            url_for("admin_produtos")
        )

    return render_template(
        "admin/produto_form.html",
        categorias=categorias,
        produto=produto
    )


@app.route(
    "/admin/produtos/<int:produto_id>/status",
    methods=["POST"]
)
def alterar_status_produto(produto_id):
    produto = Produto.query.get_or_404(
        produto_id
    )

    produto.disponivel = not produto.disponivel

    db.session.commit()

    flash(
        "Disponibilidade do produto atualizada.",
        "sucesso"
    )

    return redirect(
        url_for("admin_produtos")
    )


@app.route(
    "/admin/produtos/<int:produto_id>/excluir",
    methods=["POST"]
)
def excluir_produto(produto_id):
    produto = Produto.query.get_or_404(
        produto_id
    )

    excluir_imagem(produto.imagem)

    db.session.delete(produto)
    db.session.commit()

    flash(
        "Produto excluído com sucesso.",
        "sucesso"
    )

    return redirect(
        url_for("admin_produtos")
    )


# =========================================================
# DADOS INICIAIS
# =========================================================

def criar_dados_iniciais():
    configuracao = Configuracao.query.first()

    if not configuracao:
        configuracao = Configuracao(
            nome_loja="Nunes Delivery",
            descricao="Seu pedido, rápido e fácil.",
            telefone="",
            chave_pix="",
            taxa_entrega=5.00,
            pedido_minimo=0.00,
            loja_aberta=True
        )

        db.session.add(configuracao)

    if Categoria.query.count() == 0:
        lanches = Categoria(
            nome="Lanches",
            ordem=1
        )

        combos = Categoria(
            nome="Combos",
            ordem=2
        )

        porcoes = Categoria(
            nome="Porções",
            ordem=3
        )

        bebidas = Categoria(
            nome="Bebidas",
            ordem=4
        )

        db.session.add_all([
            lanches,
            combos,
            porcoes,
            bebidas
        ])

        db.session.flush()

        produtos = [
            Produto(
                nome="X-Bacon Especial",
                descricao=(
                    "Pão, hambúrguer, bacon, queijo, "
                    "salada e molho especial."
                ),
                preco=29.90,
                emoji="🍔",
                disponivel=True,
                destaque=True,
                categoria_id=lanches.id
            ),
            Produto(
                nome="X-Salada",
                descricao=(
                    "Pão, hambúrguer, queijo, salada "
                    "e molho da casa."
                ),
                preco=24.90,
                emoji="🍔",
                disponivel=True,
                destaque=False,
                categoria_id=lanches.id
            ),
            Produto(
                nome="Combo Nunes",
                descricao=(
                    "X-Bacon, batata pequena "
                    "e refrigerante em lata."
                ),
                preco=39.90,
                emoji="🍔",
                disponivel=True,
                destaque=True,
                categoria_id=combos.id
            ),
            Produto(
                nome="Batata com Cheddar e Bacon",
                descricao=(
                    "Batata frita crocante com "
                    "cheddar e bacon."
                ),
                preco=24.90,
                emoji="🍟",
                disponivel=True,
                destaque=False,
                categoria_id=porcoes.id
            ),
            Produto(
                nome="Refrigerante em Lata",
                descricao="Escolha o sabor disponível.",
                preco=6.00,
                emoji="🥤",
                disponivel=True,
                destaque=False,
                categoria_id=bebidas.id
            )
        ]

        db.session.add_all(produtos)

    db.session.commit()


# =========================================================
# INICIAR
# =========================================================

def iniciar_banco():
    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    with app.app_context():
        db.create_all()
        criar_dados_iniciais()


iniciar_banco()


if __name__ == "__main__":
    porta = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=porta,
        debug=False
    )