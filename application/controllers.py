# ------------------------------------------------------------
# --------------file contains controllers for user-----------
# ------------------------------------------------------------

from flask import request, render_template, url_for, redirect, flash
from datetime import datetime
from decimal import Decimal

from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask import current_app as app
from application.models import *
from application.functions import *

#-------initiallize login manager--------------
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

# -------------------------------------------
# ----------controller for  login------------
# -------------------------------------------


# controller for login user
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        page = "login"
        submit_name="Sign In"
        return render_template("login.html",page=page, submit_name = submit_name)
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return redirect('/')
            else:
                flash("Wrong Password")
                return redirect("/login")
        else:
            flash("You are not registerd")
            return redirect("/login")


# controller to register user
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        page = "register"
        submit_name="Register"
        return render_template("login.html",page=page, submit_name=submit_name)
    if request.method == "POST":
        email = request.form["email"]
        existing_email = User.query.filter_by(email = email).first()
        if existing_email:
            flash("email already register")
            return redirect("/login")
        else:
            password = request.form["password"]
            hashed_password = bcrypt.generate_password_hash(password)
            new_user= User(email=email,password = hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("You are now registered, Please Login.")
            return redirect("/login")


# controller to change password for user
@app.route("/forget_password",methods=["GET","POST"])
def forget_password():
    if request.method == "GET":
        page = "forget_password"
        submit_name="Change Password"
        return render_template("login.html",page=page, submit_name=submit_name)
    if request.method == "POST":
        email = request.form["email"]
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            new_password = request.form["password"]
            hashed_password = bcrypt.generate_password_hash(new_password)
            existing_user.password = hashed_password
            db.session.commit()
            flash("Password changed,Login with new.")
            return redirect('/login')
        else:
            flash("You are not registered. Register Now!")
            return redirect('/register')


# home page controller
@app.route("/", methods=["GET","POST"])
@login_required
def home():
    if request.method== "GET":
        email = current_user.email
        user = email.split("@")[0]
        shows = Show.query.all()
        # make list for filter of loaction and genere tag
        show_venues = Show_venue.query.join(Show,  Venue).filter(Show_venue.show_id == Show.show_id).filter(Show_venue.venue_id == Venue.venue_id).add_columns(Venue.place,Show.show_tag,Show_venue.show_timing).all()
        shows_not_unique_tags=[]
        shows_not_unique_locations=[]
        for show_venue in show_venues:
            shows_not_unique_tags.append(show_venue[2])
            show_start_time = show_start_time = datetime.strptime(str(show_venue[3]), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
            if (show_start_time > datetime.now()):
                shows_not_unique_locations.append(show_venue[1])
        shows_locations = set(shows_not_unique_locations)
        shows_tags = set(shows_not_unique_tags)
        # show rating show id as key and rating as value
        show_rating_templates ={}
        for show in shows:
            show_rating = Show_rating.query.filter_by(show_id= show.show_id).first()
            if show_rating != None:
                rating_avg = show_rating.rating / show_rating.no_of_rating
                show_rating_templates[show.show_id] = str(Decimal(rating_avg).quantize(Decimal("1.0")))+"/"+"5"+"  "+ str(show_rating.no_of_rating)+" votes"
            else:
                show_rating_templates[show.show_id] = "None"
        return render_template("home.html",filter_result = False,show_rating_templates=show_rating_templates, filter_by_location = "True",filter_by_tag="True",filter_by_rate="True",user=user,shows = shows,shows_tags=shows_tags ,shows_locations = shows_locations, heading1= "Recently Added")



# make search page and also push search results
@app.route("/search", methods=["GET","POST"])
def search():
    if request.method == "GET":
        email = current_user.email
        user = email.split("@")[0]
        return render_template("search.html",user=user)
    if request.method == "POST":
        email = current_user.email
        user = email.split("@")[0]
        q = request.form['q']
        query = "%" + q + "%"
        # pull search result for shows
        show_name_match = []
        show_results = Show.query.filter(Show.show_name.like(query)).all()
        if show_results:
            for result in show_results:
                show_name_match.append((result.show_id,result.show_name,result.show_tag))
        # pull search result for venues
        venue_name_match = []
        venue_results = Venue.query.filter(Venue.venue_name.like(query)).all()
        if venue_results:
            for result in venue_results:
                venue_name_match.append((result.venue_id,result.venue_name,result.place))
        # pull search result for show tags
        show_tag_match =[]
        show_result_tags = Show.query.filter(Show.show_tag.like(query)).all()
        if show_result_tags:
            for result in show_result_tags:
                show_tag_match.append((result.show_id,result.show_name,result.show_tag))
        return render_template("search.html",user=user,results=True,show_name_match=show_name_match,venue_name_match=venue_name_match,show_tag_match=show_tag_match)


# controller for profile of user
# important functionally to display booked tickets by user
# and delete only those ticket whose shows is yet to start
# --------Delete ticket booked ticket------------------ 
@app.route('/profile')
@login_required
def profile():
    user_email=current_user.email
    user_name = user_email.split("@")[0]
    user_id = current_user.id
    tickets_booked_by_user = Ticket_booked.query.filter_by(user_id=user_id).all()
    upcoming_shows_ticket_details =[]
    past_show_ticket_details = []
    no_ticket_booked=False
    if tickets_booked_by_user == []:
        no_ticket_booked = True 
    elif tickets_booked_by_user != []:
        for ticket_booked_by_user in tickets_booked_by_user:
            dict={}
            show_venue_id=ticket_booked_by_user.show_venue_id
            show_venue = Show_venue.query.join(Show, Venue).filter(Show_venue.show_venue_id==show_venue_id).filter(Show_venue.venue_id== Venue.venue_id).filter(Show_venue.show_id == Show.show_id).add_columns(Show.show_name,Show.show_lang,Venue.venue_name,Venue.place,Venue.location,Show_venue.show_timing,Show.show_image_path).first()
            show_start_time = datetime.strptime(str(show_venue[6]), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
            if (show_start_time >= datetime.now()):
                dict["booking_id"] = ticket_booked_by_user.booking_id
                dict["show"]  = str(show_venue[1]) + "(" + str(show_venue[2]) + ")" #show name with show language
                dict["venue"] = str(show_venue[3]) + " " + str(show_venue[4])  #venue name with venue place
                dict["venue_location"] = show_venue[5]   #venue location
                dict["show_timming"] = str(show_venue[6])[11:16] + "pm |" + str(show_venue[6])[:10]
                dict["image_path"] = show_venue[7]
                dict["quantity"] = ticket_booked_by_user.number_of_ticket_booked
                dict["ticket_price"] = ticket_booked_by_user.cost_at_the_time_ticket_booking
                upcoming_shows_ticket_details.append(dict)
            elif (show_start_time < datetime.now()):
                dict["booking_id"] = ticket_booked_by_user.booking_id
                dict["show"]  = str(show_venue[1]) + "(" + str(show_venue[2]) + ")" + " (past)" #show name with show language
                dict["venue"] = str(show_venue[3]) + " " + str(show_venue[4])  #venue name with venue place
                dict["venue_location"] = show_venue[5]   #venue location
                dict["show_timming"] = str(show_venue[6])[11:16] + "pm |" + str(show_venue[6])[:10]
                dict["image_path"] = show_venue[7]
                dict["quantity"] = ticket_booked_by_user.number_of_ticket_booked
                dict["ticket_price"] = ticket_booked_by_user.cost_at_the_time_ticket_booking
                past_show_ticket_details.append(dict)
    return render_template("profile.html",no_ticket_booked=no_ticket_booked, user_email=user_email,user_name=user_name,upcoming_shows_ticket_details=upcoming_shows_ticket_details,past_show_ticket_details=past_show_ticket_details)


# filter by location controller
@app.route("/filter_by_location/<place>")
@login_required
def filter_by_location(place):
    email = current_user.email
    user = email.split("@")[0]
    show_venues = Show_venue.query.join(Show,  Venue).filter(Show_venue.show_id == Show.show_id).filter(Show_venue.venue_id == Venue.venue_id).filter(Venue.place == place).add_columns(Show_venue.show_id,Show_venue.show_timing).all()
    
    #show ids with booking online
    not_unique_show_ids =[]
    for  show_venue in show_venues:
            show_start_time = datetime.strptime(str(show_venue.show_timing), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
            if (show_start_time > datetime.now()):
                not_unique_show_ids.append(show_venue[1])
    # get unique ids whose booking is online
    unique_show_ids = set(not_unique_show_ids)

    shows=[]
    for show_id in unique_show_ids:
        shows.append(Show.query.filter_by(show_id=show_id).first())
    heading1= str("Shows in ") + place

    show_rating_templates ={}
    for show in shows:
        show_rating = Show_rating.query.filter_by(show_id= show.show_id).first()
        if show_rating != None:
            rating_avg = show_rating.rating / show_rating.no_of_rating
            show_rating_templates[show.show_id] = str(Decimal(rating_avg).quantize(Decimal("1.0")))+"/"+"5"+"  "+ str(show_rating.no_of_rating)+" votes"
        else:
            show_rating_templates[show.show_id] = "None"
    return render_template("home.html",filter_result=True,show_rating_templates=show_rating_templates, user=user, filter_by_location = "False",filter_by_tag = "False", shows=shows,heading1=heading1)


# filter by tag controller
@app.route("/filter_by_tag/<tag>")
@login_required
def filter_by_tag(tag):
    email = current_user.email
    user = email.split("@")[0]
    show_venues = Show_venue.query.join(Show,  Venue).filter(Show_venue.show_id == Show.show_id).filter(Show_venue.venue_id == Venue.venue_id).filter(Show.show_tag == tag).add_columns(Show_venue.show_id,Show_venue.show_timing).all()
    
    
    #unique show ids
    not_unique_show_ids =[]
    for show_venue in show_venues:
        not_unique_show_ids.append(show_venue[1])
    unique_show_ids = set(not_unique_show_ids)

    shows=[]
    for show_id in unique_show_ids:
        shows.append(Show.query.filter_by(show_id=show_id).first())
    heading1 = tag + str(" Genere Shows")

    show_rating_templates ={}
    for show in shows:
        show_rating = Show_rating.query.filter_by(show_id= show.show_id).first()
        if show_rating != None:
            rating_avg = show_rating.rating / show_rating.no_of_rating
            show_rating_templates[show.show_id] = str(Decimal(rating_avg).quantize(Decimal("1.0")))+"/"+"5"+"  "+ str(show_rating.no_of_rating)+" votes"
        else:
            show_rating_templates[show.show_id] = "None"
    return render_template("home.html",show_rating_templates=show_rating_templates, filter_result=True,user = user, filter_by_location = "False", filter_by_tag="False",shows=shows, heading1 = heading1)

# filter by tag controller
@app.route("/filter_by_rating/<int:rate>")
@login_required
def filter_by_rating(rate):
    email = current_user.email
    user = email.split("@")[0]
    show_ratings = Show_rating.query.all()

    show_ids_with_filtered_rating = []
    for show_rating in show_ratings:
        if rate + 1.1>show_rating.rating/show_rating.no_of_rating > rate:
            show_ids_with_filtered_rating.append(show_rating.show_id)

    shows=[]
    for show_id in show_ids_with_filtered_rating:
        shows.append(Show.query.filter_by(show_id=show_id).first())
    heading1 =  "Shows with " + str(rate) + " rating"

    show_rating_templates ={}
    for show in shows:
        show_rating = Show_rating.query.filter_by(show_id= show.show_id).first()
        if show_rating != None:
            rating_avg = show_rating.rating / show_rating.no_of_rating
            show_rating_templates[show.show_id] = str(Decimal(rating_avg).quantize(Decimal("1.0")))+"/"+"5"+"  "+ str(show_rating.no_of_rating)+" votes"
        else:
            show_rating_templates[show.show_id] = "None"
    return render_template("home.html",show_rating_templates=show_rating_templates, filter_result=True,user = user, filter_by_location = "False", filter_by_tag="False",shows=shows, heading1 = heading1)


@app.route('/show_page/<int:id>')
@login_required
def show_page(id):
    show=Show.query.filter_by(show_id = id).first()
    show_venues = Show_venue.query.join(Show, Venue).filter(Show_venue.show_id == id).filter(Show_venue.venue_id== Venue.venue_id).add_columns(Venue.venue_name,Venue.place,Show_venue.show_venue_id,Venue.capacity,Show_venue.show_price,Show_venue.show_timing,Show_venue.show_price).all()
    no_show=False
    check_availablity= True
    #attaching venue name with venue placing and making lsit with tuples
    venue_with_places=[]
    for show_venue in show_venues:
        show_start_time = datetime.strptime(str(show_venue[6]), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
        if (show_start_time >= datetime.now()):
            venue_with_places.append((show_venue[3], show_venue[1] + " (" + show_venue[2] + ")"))
    if len(venue_with_places) == 0:
        no_show =True
    
    email = current_user.email
    user = email.split("@")[0]

    #show rating in right format
    show_rating = Show_rating.query.filter_by(show_id= id).first()
    if show_rating != None:
        rating_avg = show_rating.rating / show_rating.no_of_rating
        rate_template = str(Decimal(rating_avg).quantize(Decimal("1.0")))+"/"+"5"+"  "+ str(show_rating.no_of_rating)+" votes"
    else:
        rate_template = "None"
    
    show_venue_id_with_current_price = {}
    # initiallize dynamic database

    for show_venue in show_venues:
        dynamic = Dynamic.query.filter_by(update_id = show_venue[3]).first()
        if dynamic == None:
            update_id = show_venue[3]
            seat_left = show_venue[4]
            current_price = show_venue[5]
            record = Dynamic(update_id,seat_left,current_price)
            db.session.add(record)
            db.session.commit()
            show_venue_id_with_current_price[show_venue[3]] = current_price
    
    #calculating and collecting dynamic price

    for show_venue in show_venues:
        show_start_time = datetime.strptime(str(show_venue[6]), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
        if (show_start_time >= datetime.now()):
            dynamic = Dynamic.query.filter_by(update_id = show_venue[3]).first()
            starting_price_of_ticket =show_venue[7]
            show_start_time = show_venue[6]
            total_seats= show_venue[4]
            update_price = calculate_dynamic_cost(dynamic.seat_left,total_seats,starting_price_of_ticket,show_start_time)
            dynamic.current_price = update_price
            db.session.commit()
            show_venue_id_with_current_price[show_venue[3]] = update_price

    # Stop taking booking when time of show pass
    show_start_time = Show_venue

    # stop taking more booking in case of house full and ristricting booking more ticket than available
    seat_restriction={}
    
    for show_venue in show_venues:
        show_start_time = datetime.strptime(str(show_venue[6]), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
        if (show_start_time >= datetime.now()):
            dict={}
            dynamic = Dynamic.query.filter_by(update_id = show_venue[3]).first()
            max_ticket_at_once=9
            if dynamic.seat_left <9:
                max_ticket_at_once = dynamic.seat_left
            dict["max"]= max_ticket_at_once
            dict["no_of_seats_left"] = dynamic.seat_left
            seat_restriction[show_venue[3]] = dict
            

    return render_template("show_page.html",show_id = id,show = show,user=user,check_availablity=check_availablity,venue_with_places=venue_with_places,no_show=no_show,rate_template=rate_template,show_venue_id_with_current_price=show_venue_id_with_current_price,seat_restriction=seat_restriction)

@app.route("/check_availablity/<int:id>",methods=["POST"])
def check_availablity(id):
    show_venue_id = int(request.form["show_venue_id"])
    take_booking =True

    show=Show.query.filter_by(show_id = id).first()
    show_venues = Show_venue.query.join(Show, Venue).filter(Show_venue.show_venue_id == show_venue_id).filter(Show_venue.venue_id== Venue.venue_id).add_columns(Venue.venue_name,Venue.place,Show_venue.show_venue_id,Venue.capacity,Show_venue.show_price,Show_venue.show_timing,Show_venue.show_price).all()
    no_show=False

    # attaching venue name with venue placing and making dictionary
    venue_with_places=[]
    for show_venue in show_venues:
        show_start_time = datetime.strptime(str(show_venue[6]), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
        if (show_start_time >= datetime.now()):
            venue_with_places.append((show_venue[3], show_venue[1] + " (" + show_venue[2] + ")"))
    if len(venue_with_places) == 0:
        no_show =True
    
    email = current_user.email
    user = email.split("@")[0]

    #show raing in right format
    show_rating = Show_rating.query.filter_by(show_id= id).first()
    if show_rating != None:
        rating_avg = show_rating.rating / show_rating.no_of_rating
        rate_template = str(Decimal(rating_avg).quantize(Decimal("1.0")))+"/"+"5"+"  "+ str(show_rating.no_of_rating)+" votes"
    else:
        rate_template = "None"

    # stop taking more booking in case of house full and ristricting booking more ticket than available
    dynamic = Dynamic.query.filter_by(update_id = show_venue_id).first()
    max_ticket_at_once=9
    if dynamic.seat_left <9:
        max_ticket_at_once = dynamic.seat_left
    max= max_ticket_at_once
    no_of_seats_left = dynamic.seat_left
    cost_per_ticket = dynamic.current_price

    house_full=False
    if no_of_seats_left == 0:
        no_show = False
        take_booking = False
        house_full = True

    return render_template("show_page.html",house_full=house_full,show = show,user=user,max=max,cost_per_ticket=cost_per_ticket ,no_of_seats_left=no_of_seats_left, take_booking=take_booking,show_venue_id=show_venue_id,no_show=no_show,rate_template=rate_template,venue_with_places=venue_with_places)#,show_venue_id_with_current_price=show_venue_id_with_current_price) 

@app.route("/book_ticket/<int:id>",methods=["POST"])
@login_required
def book_ticket(id):
    user_id = current_user.id
    show_venue_id = id
    number_of_ticket_booked = request.form["no_of_ticket"]
    dynamic = Dynamic.query.filter_by(update_id = show_venue_id).first()
    dynamic.seat_left = int(dynamic.seat_left) - int(number_of_ticket_booked)
    cost_at_the_time_of_ticket_booking = dynamic.current_price
    time_of_ticket_booked = datetime.now()
    record = Ticket_booked(user_id,show_venue_id,number_of_ticket_booked,cost_at_the_time_of_ticket_booking,time_of_ticket_booked)
    db.session.add(record)
    db.session.commit()
    return redirect("/profile")

@app.route("/add_rating/<int:id>",methods=["POST"])
@login_required
def add_rating(id):
    show_id = id
    rating = request.form["rating"]
    show_rating = Show_rating.query.filter_by(show_id = show_id).first()
    if show_rating == None:
        no_of_rating = 1
        record = Show_rating(show_id, rating,no_of_rating)
        db.session.add(record)
        db.session.commit()
        return redirect(url_for("show_page", id = show_id))
    else:
        show_rating.rating += int(rating)
        show_rating.no_of_rating += 1
        db.session.commit()
        return redirect(url_for("show_page", id = show_id))
    

@app.route("/remove_booked_ticket/<int:booking_id>")
@login_required
def remove_booked_ticket(booking_id):
    ticket = Ticket_booked.query.filter_by(booking_id=booking_id).first()
    dynamic = Dynamic.query.filter_by(update_id = ticket.show_venue_id).first()
    if dynamic:
        dynamic.seat_left = dynamic.seat_left + ticket.number_of_ticket_booked
        db.session.commit()
    db.session.delete(ticket)
    db.session.commit()
    return redirect('/profile')

@app.route("/logout",methods=["GET","POST"])
@login_required
def logout():
    logout_user()
    return redirect("/login")

