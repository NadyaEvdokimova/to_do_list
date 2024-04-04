from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, DateField, SelectField
from wtforms.validators import DataRequired
from datetime import datetime
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
Bootstrap5(app)
# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Create forms
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class AddForm(FlaskForm):
    category = SelectField("Category", choices=[('1', 'Work'), ('2', 'Personal'), ('3', 'Other')], coerce=int,
                           validators=[DataRequired()])
    task = StringField("Task", validators=[DataRequired()])
    due_date = DateField("Due date", format='%Y-%m-%d', validators=[DataRequired()])
    selected = BooleanField("⭐")
    submit = SubmitField('✓')


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///to_do_list.db")
db = SQLAlchemy()
db.init_app(app)


# CONFIGURE TABLES: User table for all your registered users, category table and table for tasks
class ToDoList(db.Model):
    __tablename__ = "to_do_list"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="lists")
    task = db.Column(db.String(250), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    selected = db.Column(db.Boolean)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = relationship("Category", back_populates="tasks_list")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    lists = relationship("ToDoList", back_populates="author")


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    tasks_list = relationship('ToDoList', back_populates='category', lazy=True)


def initialize_categories():
    initial_categories = ['Work', 'Personal', 'Other']
    for category_name in initial_categories:
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
    db.session.commit()


with app.app_context():
    db.create_all()
    initialize_categories()


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/", methods=["GET", "POST"])
def home():
    if current_user.is_authenticated:
        categories = Category.query.all()
        tasks_by_category = {}
        for category in categories:
            tasks_by_category[category.name] = (ToDoList.query.filter_by(category_id=category.id,
                                                                         author_id=current_user.id)
                                                .order_by(ToDoList.due_date).all())
        form = AddForm()
        if form.validate_on_submit():
            category_id = form.category.data
            category_name = dict(form.category.choices).get(str(category_id))

            new_task = ToDoList(
                author=current_user,
                task=form.task.data,
                due_date=form.due_date.data,
                selected=form.selected.data,
                category_id=category_id
            )
            db.session.add(new_task)
            db.session.commit()
            category = Category.query.get(category_id)
            if not category:
                category = Category(id=category_id, name=category_name)
                db.session.add(category)

            db.session.commit()
            return redirect(url_for("home"))
        return render_template("index.html", form=form, current_user=current_user,
                               tasks_by_category=tasks_by_category)
    else:
        return render_template("index.html")


# Route for deleting tasks
@app.route("/delete/<int:task_id>", methods=["GET", "POST"])
def delete_task(task_id):
    if current_user.is_authenticated:
        task_to_delete = db.get_or_404(ToDoList, task_id)
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


# Route for editing tasks or due dates
@app.route('/edit_task/<int:task_id>', methods=['PATCH'])
def edit_task(task_id):
    task = ToDoList.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    data = request.json
    new_task_text = data.get('task_text')
    new_due_date_str = data.get('due_date')

    if new_task_text is not None:
        task.task = new_task_text
    if new_due_date_str is not None:
        new_due_date = datetime.strptime(new_due_date_str, '%Y-%m-%d').date()
        task.due_date = new_due_date

    db.session.commit()

    return jsonify({'success': True})


if __name__ == "__main__":
    app.run(debug=False, port=5001)
