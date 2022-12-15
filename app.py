from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User,  Feedback
from forms import UserForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///auth_exercise"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "123abc"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Oh no! Username taken. Try something different.')
            return render_template('register.html', form=form)
        session['user_id'] = new_user.id
        return redirect(f'/users/{new_user.id}')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            session['user_id'] = user.id
            return redirect(f'/users/{user.id}')
        else: 
            form.username.errors = ['Invalid username/password.']
    
    return render_template('login.html', form=form)


@app.route('/users/<int:user_id>', methods=['GET'])
def show_user(user_id):
    user = User.query.get_or_404(user_id)
    if "user_id" not in session:
        flash("Please login or sign up first!", "danger")
        return redirect('/')

    
    all_feedback = Feedback.query.all()
    
    return render_template('user_profile.html', user=user, all_feedback=all_feedback)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    if "user_id" not in session or user.id != session['user_id']:
        raise Unauthorized()

    
    db.session.delete(user)
    db.session.commit()
    session.pop("user_id")

    return redirect('/')



@app.route('/logout')
def logout_user():
    session.pop("user_id")
    flash("Goodbye!", "info")
    return redirect('/')


@app.route('/users/<int:user_id>/feedback/add', methods=['GET', 'POST'])
def get_feedback_form(user_id):
    user = User.query.get_or_404(user_id)
    if "user_id" not in session or user.id != session["user_id"]:
        raise Unauthorized()
    
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        
        new_feedback = Feedback(title=title, content=content, user_id=user.id)

        db.session.add(new_feedback)
        db.session.commit()

        return redirect(f"/users/{new_feedback.user.id}")
    
    else:
        return render_template("feedback/new.html", form=form)


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)

    if "user_id" not in session or feedback.user.id != session["user_id"]:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f'/users/{feedback.user.id}')

    return render_template("/feedback/edit.html", form=form, feedback=feedback)

@app.route("/feedback/<int:feedback_id>/delete", methods=['POST'])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)

    if "user_id" not in session or feedback.user.id != session["user_id"]:
        raise Unauthorized()

    db.session.delete(feedback)
    db.session.commit()

    return redirect(f'/users/{feedback.user.id}')


