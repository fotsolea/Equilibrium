from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
import csv
import io
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)
app.secret_key = "change-cette-cle-secrete-en-production"

TRANSLATIONS = {
    "fr": {
        "dashboard": "Tableau de bord",
        "transactions": "Transactions",
        "budgets": "Budgets",
        "analytics": "Rapports",
        "settings": "Paramètres",
        "logout": "Déconnexion",
        "export_csv": "Exporter CSV",
        "profile": "Modifier mon profil",
        "login": "Connexion",
        "register": "Créer un compte",
        "income": "Revenu",
        "expense": "Dépense",
        "amount": "Montant",
        "category": "Catégorie",
        "date": "Date",
        "description": "Description",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "delete": "Supprimer",
        "edit": "Modifier",
        "total_income": "Revenus totaux",
        "total_expense": "Dépenses totales",
        "balance": "Solde",
        "recent_transactions": "Transactions récentes",
        "spending_evolution": "Évolution des dépenses",
        "budget_status": "État des budgets",
        "monthly_budget": "Budget mensuel",
        "category_budget": "Budget par catégorie",
        "remaining": "Restant",
        "spent": "Dépensé",
        "no_data": "Aucune donnée disponible",
        "add_transaction": "Ajouter une transaction",
        "edit_transaction": "Modifier la transaction",
        "delete_transaction": "Supprimer la transaction",
        "welcome": "Bienvenue",
        "email": "Adresse e-mail",
        "password": "Mot de passe",
        "full_name": "Nom complet",
        "confirm_password": "Confirmer le mot de passe",
        "change_password": "Modifier le mot de passe",
        "current_password": "Mot de passe actuel",
        "new_password": "Nouveau mot de passe",
        "language": "Langue",
        "currency": "Devise",
        "all_categories": "Toutes les catégories",
        "all_types": "Tous les types",
        "search": "Rechercher",
        "filter": "Filtrer",
        "reset": "Réinitialiser",
        "page": "Page",
        "of": "sur",
        "results": "résultats",
        "no_results": "Aucun résultat trouvé"
    }
}


@app.context_processor
def inject_translations():
    language = session.get("language", "fr")

    def translate(key):
        return TRANSLATIONS.get(language, {}).get(key, key)

    return {
        "t": translate,
        "lang": language,
        "current_language": language
    }
    language = session.get("language", "fr")

    def translate(key):
        return TRANSLATIONS.get(
            language,
            {}
        ).get(
            key,
            key
        )

    return {
        "t": translate,
        "current_language": language
    }

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "expense_tracker"
}

TRANSACTIONS_PER_PAGE = 10


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped_view


def valid_month(value):
    try:
        datetime.strptime(value, "%Y-%m")
        return True
    except (ValueError, TypeError):
        return False


def get_selected_month():
    selected_month = request.args.get("month", date.today().strftime("%Y-%m"))

    if not valid_month(selected_month):
        selected_month = date.today().strftime("%Y-%m")

    return selected_month


def get_month_start(selected_month):
    return selected_month + "-01"


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
            return redirect(url_for("register"))

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                flash("Cet e-mail est déjà utilisé.", "error")
                return redirect(url_for("register"))

            cursor.execute(
                """
                INSERT INTO users (full_name, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (
                    full_name,
                    email,
                    generate_password_hash(password)
                )
            )
            connection.commit()

            flash("Compte créé avec succès. Connecte-toi.", "success")
            return redirect(url_for("login"))

        except Error as error:
            flash(f"Erreur de base de données : {error}", "error")
            return redirect(url_for("register"))

        finally:
            cursor.close()
            connection.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT id, full_name, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,)
            )
            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["user_name"] = user["full_name"]

                return redirect(url_for("dashboard"))

            flash("E-mail ou mot de passe incorrect.", "error")
            return redirect(url_for("login"))

        finally:
            cursor.close()
            connection.close()

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/set-language/<language>")
@login_required
def set_language(language):
    if language not in ("fr", "en"):
        language = "fr"

    session["language"] = language

    return redirect(request.referrer or url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    selected_month = get_selected_month()
    month_start = get_month_start(selected_month)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END),
                    0
                ) AS total_income,

                COALESCE(
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END),
                    0
                ) AS total_expense
            FROM transactions
            WHERE user_id = %s
              AND transaction_date >= %s
              AND transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            """,
            (user_id, month_start, month_start)
        )
        totals = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                t.id,
                t.type,
                t.amount,
                t.description,
                t.transaction_date,
                c.name AS category_name,
                c.color AS category_color
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            WHERE t.user_id = %s
              AND t.transaction_date >= %s
              AND t.transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            ORDER BY t.transaction_date DESC, t.id DESC
            LIMIT 4
            """,
            (user_id, month_start, month_start)
        )
        recent_transactions = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                c.name,
                c.color,
                COALESCE(SUM(t.amount), 0) AS total
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            WHERE t.user_id = %s
              AND t.type = 'expense'
              AND t.transaction_date >= %s
              AND t.transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            GROUP BY c.id, c.name, c.color
            ORDER BY total DESC
            """,
            (user_id, month_start, month_start)
        )
        expenses_by_category = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                DATE_FORMAT(transaction_date, '%%Y-%%m') AS month,
                COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = %s
              AND type = 'expense'
              AND transaction_date >= DATE_SUB(%s, INTERVAL 5 MONTH)
              AND transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            GROUP BY DATE_FORMAT(transaction_date, '%%Y-%%m')
            ORDER BY month
            """,
            (user_id, month_start, month_start)
        )
        spending_evolution = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                b.id,
                b.amount_limit,
                c.name AS category_name,
                c.color AS category_color,
                COALESCE(SUM(t.amount), 0) AS spent
            FROM budgets b
            JOIN categories c
                ON c.id = b.category_id
            LEFT JOIN transactions t
                ON t.user_id = b.user_id
                AND t.category_id = b.category_id
                AND t.type = 'expense'
                AND t.transaction_date >= b.budget_month
                AND t.transaction_date < DATE_ADD(b.budget_month, INTERVAL 1 MONTH)
            WHERE b.user_id = %s
              AND b.budget_month = %s
            GROUP BY
                b.id,
                b.amount_limit,
                c.name,
                c.color
            ORDER BY
                CASE
                    WHEN b.amount_limit > 0
                    THEN COALESCE(SUM(t.amount), 0) / b.amount_limit
                    ELSE 0
                END DESC
            LIMIT 2
            """,
            (user_id, month_start)
        )
        budget_status = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    total_income = float(totals["total_income"])
    total_expense = float(totals["total_expense"])
    balance = total_income - total_expense

    for budget in budget_status:
        budget["amount_limit"] = float(budget["amount_limit"])
        budget["spent"] = float(budget["spent"])

        if budget["amount_limit"] > 0:
            budget["actual_percentage"] = (
                budget["spent"] / budget["amount_limit"]
            ) * 100
            budget["percentage"] = min(
                budget["actual_percentage"],
                100
            )
        else:
            budget["actual_percentage"] = 0
            budget["percentage"] = 0

        budget["is_exceeded"] = (
            budget["spent"] > budget["amount_limit"]
        )

    return render_template(
        "dashboard.html",
        selected_month=selected_month,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        recent_transactions=recent_transactions,
        expenses_by_category=expenses_by_category,
        spending_evolution=spending_evolution,
        budget_status=budget_status
    )


@app.route("/transactions")
@login_required
def transactions():
    user_id = session["user_id"]

    selected_month = request.args.get("month", "")
    selected_type = request.args.get("type", "")
    selected_category = request.args.get("category", "")
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    offset = (page - 1) * TRANSACTIONS_PER_PAGE

    conditions = " WHERE t.user_id = %s "
    params = [user_id]

    if selected_month and valid_month(selected_month):
        conditions += (
            " AND DATE_FORMAT(t.transaction_date, '%%Y-%%m') = %s "
        )
        params.append(selected_month)

    if selected_type in ("income", "expense"):
        conditions += " AND t.type = %s "
        params.append(selected_type)

    if selected_category:
        conditions += " AND t.category_id = %s "
        params.append(selected_category)

    if search:
        conditions += """
            AND (
                t.description LIKE %s
                OR c.name LIKE %s
            )
        """
        search_value = f"%{search}%"
        params.extend([search_value, search_value])

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total_transactions
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            {conditions}
            """,
            params
        )
        total_transactions = int(
            cursor.fetchone()["total_transactions"]
        )

        total_pages = max(
            1,
            (total_transactions + TRANSACTIONS_PER_PAGE - 1)
            // TRANSACTIONS_PER_PAGE
        )

        if page > total_pages:
            page = total_pages
            offset = (page - 1) * TRANSACTIONS_PER_PAGE

        cursor.execute(
            f"""
            SELECT
                t.id,
                t.type,
                t.amount,
                t.description,
                t.transaction_date,
                c.id AS category_id,
                c.name AS category_name,
                c.color AS category_color
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            {conditions}
            ORDER BY t.transaction_date DESC, t.id DESC
            LIMIT %s OFFSET %s
            """,
            params + [TRANSACTIONS_PER_PAGE, offset]
        )
        transaction_list = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN t.type = 'income' THEN t.amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_income,

                COALESCE(
                    SUM(
                        CASE
                            WHEN t.type = 'expense' THEN t.amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_expense
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            {conditions}
            """,
            params
        )
        totals = cursor.fetchone()

        cursor.execute(
            """
            SELECT id, name, type, color
            FROM categories
            WHERE user_id IS NULL OR user_id = %s
            ORDER BY type, name
            """,
            (user_id,)
        )
        categories = cursor.fetchall()

        cursor.execute(
            """
            SELECT DISTINCT
                DATE_FORMAT(transaction_date, '%%Y-%%m') AS month
            FROM transactions
            WHERE user_id = %s
            ORDER BY month DESC
            """,
            (user_id,)
        )
        available_months = [
            row["month"]
            for row in cursor.fetchall()
            if row["month"]
        ]

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "transactions.html",
        transactions=transaction_list,
        categories=categories,
        available_months=available_months,
        selected_month=selected_month,
        selected_type=selected_type,
        selected_category=selected_category,
        search=search,
        total_income=float(totals["total_income"]),
        total_expense=float(totals["total_expense"]),
        total_transactions=total_transactions,
        page=page,
        total_pages=total_pages
    )


@app.route("/transactions/add", methods=["POST"])
@login_required
def add_transaction():
    user_id = session["user_id"]

    transaction_type = request.form.get("type")
    category_id_text = request.form.get("category_id")
    amount_text = request.form.get("amount")
    description = request.form.get("description", "").strip()
    transaction_date_text = request.form.get("transaction_date")

    if transaction_type not in ("income", "expense"):
        flash("Type de transaction invalide.", "error")
        return redirect(url_for("transactions"))

    try:
        category_id = int(category_id_text)
        amount = Decimal(amount_text)

        if amount <= 0:
            raise ValueError

        transaction_date = datetime.strptime(
            transaction_date_text,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError, InvalidOperation):
        flash("Montant, catégorie ou date invalide.", "error")
        return redirect(url_for("transactions"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE id = %s
              AND type = %s
              AND (user_id IS NULL OR user_id = %s)
            """,
            (category_id, transaction_type, user_id)
        )
        category = cursor.fetchone()

        if not category:
            flash(
                "La catégorie choisie ne correspond pas "
                "au type de transaction.",
                "error"
            )
            return redirect(url_for("transactions"))

        cursor.execute(
            """
            INSERT INTO transactions (
                user_id,
                category_id,
                type,
                amount,
                description,
                transaction_date
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                category_id,
                transaction_type,
                amount,
                description,
                transaction_date
            )
        )
        connection.commit()

        flash("Transaction ajoutée avec succès.", "success")

    except Error as error:
        flash(f"Erreur lors de l’ajout : {error}", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(
        url_for(
            "transactions",
            month=transaction_date.strftime("%Y-%m")
        )
    )


@app.route("/transactions/edit/<int:transaction_id>", methods=["POST"])
@login_required
def edit_transaction(transaction_id):
    user_id = session["user_id"]

    transaction_type = request.form.get("type")
    category_id_text = request.form.get("category_id")
    amount_text = request.form.get("amount")
    description = request.form.get("description", "").strip()
    transaction_date_text = request.form.get("transaction_date")

    if transaction_type not in ("income", "expense"):
        flash("Type de transaction invalide.", "error")
        return redirect(url_for("transactions"))

    try:
        category_id = int(category_id_text)
        amount = Decimal(amount_text)

        if amount <= 0:
            raise ValueError

        transaction_date = datetime.strptime(
            transaction_date_text,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError, InvalidOperation):
        flash("Montant, catégorie ou date invalide.", "error")
        return redirect(url_for("transactions"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE id = %s
              AND type = %s
              AND (user_id IS NULL OR user_id = %s)
            """,
            (category_id, transaction_type, user_id)
        )
        category = cursor.fetchone()

        if not category:
            flash(
                "La catégorie choisie ne correspond pas "
                "au type de transaction.",
                "error"
            )
            return redirect(url_for("transactions"))

        cursor.execute(
            """
            UPDATE transactions
            SET
                type = %s,
                category_id = %s,
                amount = %s,
                description = %s,
                transaction_date = %s
            WHERE id = %s
              AND user_id = %s
            """,
            (
                transaction_type,
                category_id,
                amount,
                description,
                transaction_date,
                transaction_id,
                user_id
            )
        )
        connection.commit()

        if cursor.rowcount == 0:
            flash("Transaction introuvable ou non autorisée.", "error")
        else:
            flash("Transaction modifiée avec succès.", "success")

    except Error as error:
        flash(f"Erreur lors de la modification : {error}", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(
        url_for(
            "transactions",
            month=transaction_date.strftime("%Y-%m")
        )
    )


@app.route("/transactions/delete/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM transactions
            WHERE id = %s
              AND user_id = %s
            """,
            (transaction_id, user_id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            flash("Transaction introuvable ou non autorisée.", "error")
        else:
            flash("Transaction supprimée.", "success")

    except Error as error:
        flash(f"Erreur lors de la suppression : {error}", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("transactions"))


@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    user_id = session["user_id"]
    selected_month = get_selected_month()
    budget_month_date = get_month_start(selected_month)

    if request.method == "POST":
        form_action = request.form.get("form_action", "")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            if form_action == "save_total_budget":
                total_budget_text = request.form.get("total_budget", "")

                try:
                    total_budget = Decimal(total_budget_text)

                    if total_budget < 0:
                        raise ValueError

                except (
                    ValueError,
                    TypeError,
                    InvalidOperation
                ):
                    flash(
                        "Le budget total doit être un montant positif.",
                        "error"
                    )
                    return redirect(
                        url_for("budgets", month=selected_month)
                    )

                cursor.execute(
                    """
                    INSERT INTO monthly_budget_totals (
                        user_id,
                        budget_month,
                        amount_limit
                    )
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        amount_limit = VALUES(amount_limit)
                    """,
                    (
                        user_id,
                        budget_month_date,
                        total_budget
                    )
                )
                connection.commit()

                flash("Budget total enregistré.", "success")

            elif form_action == "save_category_budget":
                category_id_text = request.form.get("category_id")
                amount_limit_text = request.form.get("amount_limit")

                try:
                    category_id = int(category_id_text)
                    amount_limit = Decimal(amount_limit_text)

                    if amount_limit <= 0:
                        raise ValueError

                except (
                    ValueError,
                    TypeError,
                    InvalidOperation
                ):
                    flash(
                        "Catégorie ou montant de budget invalide.",
                        "error"
                    )
                    return redirect(
                        url_for("budgets", month=selected_month)
                    )

                cursor.execute(
                    """
                    SELECT id
                    FROM categories
                    WHERE id = %s
                      AND type = 'expense'
                      AND (user_id IS NULL OR user_id = %s)
                    """,
                    (category_id, user_id)
                )
                category = cursor.fetchone()

                if not category:
                    flash(
                        "Choisis une catégorie de dépense valide.",
                        "error"
                    )
                    return redirect(
                        url_for("budgets", month=selected_month)
                    )

                cursor.execute(
                    """
                    INSERT INTO budgets (
                        user_id,
                        category_id,
                        budget_month,
                        amount_limit
                    )
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        amount_limit = VALUES(amount_limit)
                    """,
                    (
                        user_id,
                        category_id,
                        budget_month_date,
                        amount_limit
                    )
                )
                connection.commit()

                flash("Limite de budget enregistrée.", "success")

            else:
                flash("Action de budget inconnue.", "error")

        except Error as error:
            flash(f"Erreur de base de données : {error}", "error")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("budgets", month=selected_month))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT amount_limit
            FROM monthly_budget_totals
            WHERE user_id = %s
              AND budget_month = %s
            """,
            (user_id, budget_month_date)
        )
        total_budget_row = cursor.fetchone()

        total_budget = (
            float(total_budget_row["amount_limit"])
            if total_budget_row
            else 0.0
        )

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_spent
            FROM transactions
            WHERE user_id = %s
              AND type = 'expense'
              AND transaction_date >= %s
              AND transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            """,
            (user_id, budget_month_date, budget_month_date)
        )
        total_spent = float(cursor.fetchone()["total_spent"])

        cursor.execute(
            """
            SELECT
                b.id,
                b.category_id,
                b.amount_limit,
                c.name AS category_name,
                c.color AS category_color,
                COALESCE(SUM(t.amount), 0) AS spent
            FROM budgets b
            JOIN categories c
                ON c.id = b.category_id
            LEFT JOIN transactions t
                ON t.user_id = b.user_id
                AND t.category_id = b.category_id
                AND t.type = 'expense'
                AND t.transaction_date >= b.budget_month
                AND t.transaction_date < DATE_ADD(
                    b.budget_month,
                    INTERVAL 1 MONTH
                )
            WHERE b.user_id = %s
              AND b.budget_month = %s
            GROUP BY
                b.id,
                b.category_id,
                b.amount_limit,
                c.name,
                c.color
            ORDER BY c.name
            """,
            (user_id, budget_month_date)
        )
        budget_list = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, name, color
            FROM categories
            WHERE type = 'expense'
              AND (user_id IS NULL OR user_id = %s)
            ORDER BY name
            """,
            (user_id,)
        )
        expense_categories = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    for budget in budget_list:
        budget["amount_limit"] = float(budget["amount_limit"])
        budget["spent"] = float(budget["spent"])

        if budget["amount_limit"] > 0:
            budget["actual_percentage"] = (
                budget["spent"] / budget["amount_limit"]
            ) * 100
            budget["percentage"] = min(
                budget["actual_percentage"],
                100
            )
        else:
            budget["actual_percentage"] = 0
            budget["percentage"] = 0

        budget["remaining"] = (
            budget["amount_limit"] - budget["spent"]
        )

        budget["is_exceeded"] = (
            budget["spent"] > budget["amount_limit"]
        )

    total_remaining = total_budget - total_spent

    return render_template(
        "budgets.html",
        budgets=budget_list,
        expense_categories=expense_categories,
        selected_month=selected_month,
        total_budget=total_budget,
        total_spent=total_spent,
        total_remaining=total_remaining
    )


@app.route("/budgets/edit/<int:budget_id>", methods=["POST"])
@login_required
def edit_budget(budget_id):
    user_id = session["user_id"]
    selected_month = request.form.get(
        "month",
        date.today().strftime("%Y-%m")
    )
    amount_limit_text = request.form.get("amount_limit")

    if not valid_month(selected_month):
        selected_month = date.today().strftime("%Y-%m")

    try:
        amount_limit = Decimal(amount_limit_text)

        if amount_limit <= 0:
            raise ValueError

    except (ValueError, TypeError, InvalidOperation):
        flash("Le montant de la limite est invalide.", "error")
        return redirect(url_for("budgets", month=selected_month))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE budgets
            SET amount_limit = %s
            WHERE id = %s
              AND user_id = %s
            """,
            (amount_limit, budget_id, user_id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            flash("Budget introuvable ou non autorisé.", "error")
        else:
            flash("Limite de budget modifiée avec succès.", "success")

    except Error as error:
        flash(f"Erreur lors de la modification : {error}", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("budgets", month=selected_month))


@app.route("/budgets/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM budgets
            WHERE id = %s
              AND user_id = %s
            """,
            (budget_id, user_id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            flash("Budget introuvable ou non autorisé.", "error")
        else:
            flash("Limite de budget supprimée.", "success")

    except Error as error:
        flash(f"Erreur lors de la suppression : {error}", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("budgets"))


@app.route("/analytics")
@login_required
def analytics():
    user_id = session["user_id"]
    months_number = request.args.get("months", 6, type=int)
    selected_category = request.args.get("category_id", "", type=str)

    if months_number not in (6, 12):
        months_number = 6

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, name, color
            FROM categories
            WHERE type = 'expense'
              AND (user_id IS NULL OR user_id = %s)
            ORDER BY name ASC
            """,
            (user_id,)
        )
        categories = cursor.fetchall()

        category_conditions = ""
        category_params = []

        if selected_category:
            category_conditions = " AND t.category_id = %s "
            category_params.append(selected_category)

        cursor.execute(
            f"""
            SELECT
                DATE_FORMAT(t.transaction_date, '%%Y-%%m') AS month,
                COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END), 0) AS expenses
            FROM transactions t
            WHERE t.user_id = %s
              AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
              {category_conditions}
            GROUP BY DATE_FORMAT(t.transaction_date, '%%Y-%%m')
            ORDER BY month ASC
            """,
            [user_id, months_number] + category_params
        )
        monthly_evolution = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT
                c.id,
                c.name,
                c.color,
                COALESCE(SUM(t.amount), 0) AS total
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            WHERE t.user_id = %s
              AND t.type = 'expense'
              AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
              {category_conditions}
            GROUP BY c.id, c.name, c.color
            ORDER BY total DESC
            """,
            [user_id, months_number] + category_params
        )
        expenses_by_category = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT
                COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END), 0) AS total_expense
            FROM transactions t
            WHERE t.user_id = %s
              AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
              {category_conditions}
            """,
            [user_id, months_number] + category_params
        )
        totals = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    total_income = float(totals["total_income"])
    total_expense = float(totals["total_expense"])
    savings = total_income - total_expense

    return render_template(
        "analytics.html",
        categories=categories,
        selected_category=selected_category,
        months_number=months_number,
        expenses_by_category=expenses_by_category,
        monthly_evolution=monthly_evolution,
        total_income=total_income,
        total_expense=total_expense,
        savings=savings
    )
    user_id = session["user_id"]
    months_number = request.args.get("months", 6, type=int)

    if months_number not in (6, 12):
        months_number = 6

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'income' THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_income,

                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'expense' THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_expense
            FROM transactions
            WHERE user_id = %s
              AND transaction_date >= DATE_SUB(
                  CURDATE(),
                  INTERVAL %s MONTH
              )
            """,
            (user_id, months_number)
        )
        totals = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                c.name,
                c.color,
                COALESCE(SUM(t.amount), 0) AS total
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            WHERE t.user_id = %s
              AND t.type = 'expense'
              AND t.transaction_date >= DATE_SUB(
                  CURDATE(),
                  INTERVAL %s MONTH
              )
            GROUP BY
                c.id,
                c.name,
                c.color
            ORDER BY total DESC
            """,
            (user_id, months_number)
        )
        expenses_by_category = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                DATE_FORMAT(transaction_date, '%%Y-%%m') AS month,

                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'income' THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS income,

                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'expense' THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS expenses
            FROM transactions
            WHERE user_id = %s
              AND transaction_date >= DATE_SUB(
                  CURDATE(),
                  INTERVAL %s MONTH
              )
            GROUP BY DATE_FORMAT(transaction_date, '%%Y-%%m')
            ORDER BY month
            """,
            (user_id, months_number)
        )
        monthly_evolution = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    total_income = float(totals["total_income"])
    total_expense = float(totals["total_expense"])
    savings = total_income - total_expense

    return render_template(
        "analytics.html",
        expenses_by_category=expenses_by_category,
        monthly_evolution=monthly_evolution,
        months_number=months_number,
        total_income=total_income,
        total_expense=total_expense,
        savings=savings
    )


@app.route("/export/csv")
@login_required
def export_csv():
    user_id = session["user_id"]
    selected_category = request.args.get("category_id", "", type=str)
    months_number = request.args.get("months", 6, type=int)

    if months_number not in (6, 12):
        months_number = 6

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        category_name = "Toutes les catégories"
        category_conditions = ""
        category_params = []

        if selected_category:
            cursor.execute(
                """
                SELECT name
                FROM categories
                WHERE id = %s
                  AND (user_id IS NULL OR user_id = %s)
                """,
                (selected_category, user_id)
            )
            category = cursor.fetchone()

            if category:
                category_name = category["name"]
                category_conditions = " AND t.category_id = %s "
                category_params.append(selected_category)

        cursor.execute(
            f"""
            SELECT
                t.transaction_date,
                t.type,
                c.name AS category,
                t.amount,
                t.description
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            WHERE t.user_id = %s
              AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
              {category_conditions}
            ORDER BY t.transaction_date ASC, t.id ASC
            """,
            [user_id, months_number] + category_params
        )
        rows = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow(["RAPPORT DES TRANSACTIONS — EQUILIBRIUM"])
    writer.writerow(["Catégorie", category_name])
    writer.writerow(["Période", f"{months_number} derniers mois"])
    writer.writerow(["Date d'export", date.today().strftime("%d/%m/%Y")])
    writer.writerow([])

    writer.writerow([
        "Date",
        "Type",
        "Catégorie",
        "Montant (XOF)",
        "Description"
    ])

    total_income = 0.0
    total_expense = 0.0

    for row in rows:
        amount = float(row["amount"])
        transaction_type = "Revenu" if row["type"] == "income" else "Dépense"

        if row["type"] == "income":
            total_income += amount
        else:
            total_expense += amount

        writer.writerow([
            row["transaction_date"].strftime("%d/%m/%Y")
            if row["transaction_date"] else "",
            transaction_type,
            row["category"] or "",
            f"{amount:,.2f}".replace(",", " ").replace(".", ","),
            (row["description"] or "").strip()
        ])

    balance = total_income - total_expense

    writer.writerow([])
    writer.writerow(["RÉSUMÉ"])
    writer.writerow([
        "Total revenus",
        f"{total_income:,.2f}".replace(",", " ").replace(".", ",")
    ])
    writer.writerow([
        "Total dépenses",
        f"{total_expense:,.2f}".replace(",", " ").replace(".", ",")
    ])
    writer.writerow([
        "Solde",
        f"{balance:,.2f}".replace(",", " ").replace(".", ",")
    ])

    csv_data = "\ufeff" + output.getvalue()

    safe_category = category_name.replace(" ", "_").replace("/", "-")
    filename = (
        f"transactions_{safe_category}_"
        f"{date.today().strftime('%Y-%m-%d')}.csv"
    )

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        }
    )
    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                t.transaction_date,
                t.type,
                c.name AS category,
                t.amount,
                t.description
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            WHERE t.user_id = %s
            ORDER BY t.transaction_date ASC, t.id ASC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow(["RAPPORT DES TRANSACTIONS — EQUILIBRIUM"])
    writer.writerow(["Date d'export", date.today().strftime("%d/%m/%Y")])
    writer.writerow([])

    writer.writerow([
        "Date",
        "Type",
        "Catégorie",
        "Montant (XOF)",
        "Description"
    ])

    total_income = 0.0
    total_expense = 0.0

    for row in rows:
        amount = float(row["amount"])
        transaction_type = "Revenu" if row["type"] == "income" else "Dépense"

        if row["type"] == "income":
            total_income += amount
        else:
            total_expense += amount

        writer.writerow([
            row["transaction_date"].strftime("%d/%m/%Y")
            if row["transaction_date"] else "",
            transaction_type,
            row["category"] or "",
            f"{amount:,.2f}".replace(",", " ").replace(".", ","),
            (row["description"] or "").strip()
        ])

    balance = total_income - total_expense

    writer.writerow([])
    writer.writerow(["RÉSUMÉ"])
    writer.writerow(["Total revenus", f"{total_income:,.2f}".replace(",", " ").replace(".", ",")])
    writer.writerow(["Total dépenses", f"{total_expense:,.2f}".replace(",", " ").replace(".", ",")])
    writer.writerow(["Solde", f"{balance:,.2f}".replace(",", " ").replace(".", ",")])

    csv_data = "\ufeff" + output.getvalue()
    filename = f"transactions_equilibrium_{date.today().strftime('%Y-%m-%d')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        }
    )
    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                t.id,
                t.transaction_date,
                t.type,
                c.name AS category,
                t.amount,
                t.description
            FROM transactions t
            JOIN categories c
                ON c.id = t.category_id
            WHERE t.user_id = %s
            ORDER BY t.transaction_date DESC, t.id DESC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "ID",
            "Date",
            "Type",
            "Catégorie",
            "Montant",
            "Description"
        ]
    )

    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["transaction_date"],
                row["type"],
                row["category"],
                row["amount"],
                row["description"] or ""
            ]
        )

    csv_data = output.getvalue()
    filename = (
        f"transactions_{date.today().strftime('%Y-%m-%d')}.csv"
    )

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            f"attachment; filename={filename}"
        }
    )


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        currency = request.form.get("currency", "XOF")

        if not full_name or not email:
            flash("Le nom et l’adresse e-mail sont obligatoires.", "error")

            cursor.close()
            connection.close()

            return redirect(url_for("settings"))

        try:
            cursor.execute(
                """
                UPDATE users
                SET
                    full_name = %s,
                    email = %s,
                    currency = %s
                WHERE id = %s
                """,
                (full_name, email, currency, user_id)
            )
            connection.commit()

            session["user_name"] = full_name
            flash("Profil mis à jour avec succès.", "success")

        except Error as error:
            flash(f"Erreur lors de la mise à jour : {error}", "error")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("settings"))

    try:
        cursor.execute(
            """
            SELECT id, full_name, email, currency
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    return render_template("settings.html", user=user)


@app.route("/settings/change-password", methods=["POST"])
@login_required
def change_password():
    user_id = session["user_id"]

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if new_password != confirm_password:
        flash(
            "Les nouveaux mots de passe ne correspondent pas.",
            "error"
        )
        return redirect(url_for("settings"))

    if len(new_password) < 6:
        flash(
            "Le nouveau mot de passe doit contenir au moins 6 caractères.",
            "error"
        )
        return redirect(url_for("settings"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"],
            current_password
        ):
            flash("Le mot de passe actuel est incorrect.", "error")
            return redirect(url_for("settings"))

        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
            """,
            (generate_password_hash(new_password), user_id)
        )
        connection.commit()

        flash("Mot de passe modifié avec succès.", "success")

    except Error as error:
        flash(f"Erreur lors de la modification : {error}", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("settings"))


if __name__ == "__main__":
    app.run(debug=True)