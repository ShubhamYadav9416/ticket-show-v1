# ------------------------------------------------------------
# --------------file contains controllers for admin-----------
# ------------------------------------------------------------

from flask import request, render_template, redirect, flash, session
from sqlalchemy import delete
from datetime import datetime
from matplotlib import pyplot as plt

from flask import current_app as app
from application.models import *

# -------------------------------------
# ------uses session to login admin----
# -------------------------------------


# for first rendering template admin.html for admin login and then login admin
@app.route("/admin_login", methods=["GET","POST"])
def admin_login():
    # for rendering admin login page
    if request.method == "GET":
        submit_name="Sign In"
        return render_template("login.html",admin="True" , submit_name=submit_name)
    
    # get email and password and check those and then login admin
    # username for admin = admin_user@gmail.com
    # password for admin = 1234
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if (email == "admin_user@gmail.com" and password=="1234"):
            session['email'] = email
            return redirect('/admin')
        else:
            flash('You are not allowed to acess admin page')
            return redirect('/login')


# for logout user
@app.route("/admin_logout")
def admin_logout():
    session.pop('email',None)
    return redirect('/login')


# ---------------------------------------
# ----------dashboard controllers --------
# ----------------------------------------



@app.route("/admin")
def admin():
    if ('email' in session):
        dashboard=True

        # find total sale and total  ticket booked.
        tickets = Ticket_booked.query.all()
        total_ticket_booked = 0
        total_sale = 0
        for ticket in tickets:
            total_ticket_booked += ticket.number_of_ticket_booked 
            total_sale += ticket.cost_at_the_time_ticket_booking * ticket.number_of_ticket_booked 

        # find top rating of all show (float)
        # and 
        # top 3 rated show (list)=> each element => (rank,show name,rating of show)
        shows_ratings = Show_rating.query.select_from(Show).filter(Show_rating.show_id == Show.show_id).add_columns(Show.show_name,Show_rating.show_id,Show_rating.rating,Show_rating.no_of_rating).all()
        rating_with_show_id = {}
        top_rated_show_rating = 0
        top_3_rated_shows = []

        if shows_ratings:
            for show_rating in shows_ratings:
                rating_with_show_id[show_rating.show_id] = show_rating.rating / show_rating.no_of_rating
            sorted_dict_rating_with_show_ids = sorted(rating_with_show_id.items(),key=lambda x: x[1]) #sorted with values
            low_to_high_show_rating_show_ids = [item[0] for item in sorted_dict_rating_with_show_ids]
            top_rated_show_rating = "{0:.1f}".format(sorted_dict_rating_with_show_ids[-1][1])
            
            rank= len(low_to_high_show_rating_show_ids)
            for low_to_high_show_rating_show_id in low_to_high_show_rating_show_ids:
                for show_rating in shows_ratings:
                    if (low_to_high_show_rating_show_id == show_rating.show_id):
                        show = (rank,show_rating.show_name[0:8],show_rating.no_of_rating,"{0:.1f}".format(show_rating.rating / show_rating.no_of_rating))
                        top_3_rated_shows = [show] + top_3_rated_shows
                        rank = rank -1
        top_3_rated_shows = top_3_rated_shows[:3]

        #find total user registered
        users = User.query.all()
        total_user =0
        for user in users:
            total_user = total_user+1

        #find no of shows booking running in any venue
        show_venues = Show_venue.query.all()
        shows_booking_running = 0
        for  show_venue in show_venues:
            show_start_time = datetime.strptime(str(show_venue.show_timing), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
            if (show_start_time > datetime.now()):
                shows_booking_running = shows_booking_running +1
        
        # find top 3 revenue generating shows
        # find show name with ticket booked for that show
        shows = Show.query.all()
        # get lsit of all show_ids in as list of integer
        show_ids =[]
        for show in shows:
            show_ids.append(show.show_id)
        # get dict with show id as key and with show venue id as value in list for key
        show_ids_with_show_venue_ids = {}
        for show_id in show_ids:
            show_venue_ids = []
            show_venues = Show_venue.query.filter_by(show_id = show_id).all()
            for show_venue in show_venues:
                show_venue_ids.append(show_venue.show_venue_id)
            show_ids_with_show_venue_ids[show_id] = show_venue_ids
        tickets=Ticket_booked.query.all()
        show_id_with_collection={}
        show_id_with_ticket_booked ={}
        for show_id in show_ids:
            show_id_with_collection[show_id] = 0
            show_id_with_ticket_booked[show_id] = 0
        for show_id in show_ids:
            ticket_booked_of_each_show_id =0
            collection_of_each_show_id = 0
            for show_venue_id in show_ids_with_show_venue_ids[show_id]:
                ticket_booked_of_each_show_venue_id =0
                collection_of_each_show_venue_id = 0
                for ticket in tickets:
                    if ticket.show_venue_id == show_venue_id:
                        collection_of_each_show_venue_id += ticket.number_of_ticket_booked * ticket.cost_at_the_time_ticket_booking
                        ticket_booked_of_each_show_venue_id += ticket.number_of_ticket_booked
                collection_of_each_show_id += collection_of_each_show_venue_id
                ticket_booked_of_each_show_id += ticket_booked_of_each_show_venue_id
            show_id_with_collection[show_id] += collection_of_each_show_id
            show_id_with_ticket_booked[show_id] += ticket_booked_of_each_show_id
        
        sorted_dict_revenue_with_show_ids= sorted(show_id_with_collection.items(),key=lambda x: x[1]) #sorted with values
        low_to_high_show_revenue_show_ids = [item[0] for item in sorted_dict_revenue_with_show_ids]
       
        top_3_revenue_shows =[]
        rank = len(low_to_high_show_revenue_show_ids)
        for low_to_high_show_revenue_show_id in low_to_high_show_revenue_show_ids:
            for show in shows:
                if show.show_id == low_to_high_show_revenue_show_id:
                    show_name_with_revenue = (rank,(show.show_name)[0:8],show_id_with_collection[low_to_high_show_revenue_show_id])
                    top_3_revenue_shows = [show_name_with_revenue] + top_3_revenue_shows
                    rank =rank -1
        top_3_revenue_shows = top_3_revenue_shows[:3]
        # plot bar chart of shows ticket booking save it in static
        x=[]
        y=[]
        for show in shows:
            x.append(show.show_name[0:8])
            y.append(show_id_with_ticket_booked[show.show_id])
        plt.bar(x,y)
        plt.xlabel("Shows")
        plt.ylabel("Ticket booked")
        plt.title("Shows with ticket booked")
        plt.savefig('./static/image/show_ticket_booked_bar.png')

        return render_template('admin.html',dashboard=dashboard,total_sale=total_sale,total_ticket_booked=total_ticket_booked,top_rated_show_rating=top_rated_show_rating,top_3_rated_shows=top_3_rated_shows,total_user=total_user,shows_booking_running=shows_booking_running,top_3_revenue_shows=top_3_revenue_shows)
    else:
        return ("You are not allowed to access admin page")


# --------------------------------------
# ---------CRUD for venue --------------
# --------------------------------------


# ------------Read venues --------------
@app.route('/venue_admin', methods=["GET","POST"])
def venue():
        if ('email' in session):
            venues = Venue.query.all()
            heading = "All Venues"
            main_contents = venues
            heads = ["No.", "Venue Name", "Capacity", "Place", "Location", "Action"]
            box_contents = ["venue_id" , "venue_name" , "capacity" , "location", "place"]
            url1 = "edit_venue" 
            url2 = "delete_venue"
            id = "venue_id"
            button_url ="add_venue"
            button = "Add Venue"
            return render_template('admin.html',display_table = "True", take_input = "False", edit_delete = "True" ,input_button="True", heading=heading, main_contents = main_contents, heads = heads, box_contents = box_contents, button_url = button_url, button_name = button, url1 = url1, url2 = url2, id = id)
        else:
            return ("You are not allowed to access admin page")


# ----------Create venue -----------------
@app.route('/add_venue',methods=["GET","POST"])
def add_venue():
    if ('email' in session):
        if request.method == "GET":
            heading = "Add Venues"
            form_conditions = [{"type": "text", "name": "venue_name", "placeholder" : "venue", "required": "True"}, {"type": "number", "name": "capacity", "placeholder" : "capacity", "required": "True"}, {"type": "text", "name": "place", "placeholder" : "place", "required": "True"}, {"type": "text", "name": "location", "placeholder" : "location", "required": "True"}]
            return render_template("admin.html", take_input="True",special_form="False", display_table = "False", heading=heading, form_conditions=form_conditions)
        if request.method == "POST":
            venue_name = request.form['venue_name']
            capacity = request.form['capacity']
            place = request.form['place']
            location = request.form['location']
            record=Venue(venue_name ,capacity,place,location )
            db.session.add(record)
            db.session.commit()
            return redirect('/venue_admin')
    else:
        return ("You are not allowed to access admin page")


# -----------------Update venue ---------------- 
@app.route('/edit_venue/<int:id>',methods=["POST","GET"])
def edit_venue(id):
    if ('email' in session):
        if request.method == "GET":
            content=Venue.query.filter_by(venue_id=id).first()
            return render_template('edit_venue.html', content=content)
        if request.method=="POST":
            content = Venue.query.filter_by(venue_id=id).first()
            content.venue_name = request.form['venue_name']
            content.capacity = request.form['capacity']
            content.place = request.form['place']
            content.location = request.form['location']
            db.session.commit()
            return redirect('/venue_admin')
    else:
        return ("You are not allowed to access admin page")



# -----------Delete venue----------------------
@app.route("/delete_venue/<int:id>")
def delete_venue(id):
    if ('email' in session):
        show_venues= Show_venue.query.filter_by(venue_id = id).all()
        for show_venue in show_venues:
            dynamic = Dynamic.query.filter_by(update_id = show_venue.show_venue_id).first()
            if dynamic:
                db.session.delete(dynamic)
                db.session.commit()
            content_linked = delete(Ticket_booked).where(Ticket_booked.show_venue_id == show_venue.show_venue_id)
            db.session.execute(content_linked)
            db.session.commit()

        content_linked = delete(Show_venue).where(Show_venue.venue_id == id)
        db.session.execute(content_linked)
        db.session.commit()
        content=Venue.query.filter_by(venue_id=id).first()
        db.session.delete(content)
        db.session.commit()
        return redirect('/venue_admin')
    else:
        return ("You are not allowed to access admin page")

# --------------------------------------
# ----------CRUD Show-------------------
# --------------------------------------


# ----------Read Show-------------------
@app.route('/show_admin', methods=["GET","POST"])
def show():
    if ('email' in session):
        shows = Show.query.all()
        heading = "All Show"
        main_contents = shows
        heads = ["No.", "Show Name", "Tags","Language","Duration", "Discription", "Poster", "Action"]
        box_contents = ["show_id" , "show_name" , "show_tag","show_lang", "show_duration", "show_discription"]
        additional1 = ["show_image_path"]
        url1 = "edit_show" 
        url2 = "delete_show"
        id = "show_id"
        button_url ="add_show"
        button = "Add Show"
        return render_template('admin.html',display_table = "True", take_input = "False", edit_delete = "True" ,input_button="True",heading=heading, main_contents = main_contents, heads = heads, box_contents = box_contents, additional1 = additional1, button_url = button_url, button_name = button, url1 = url1, url2 = url2, id = id)
    else:
        return ("You are not allowed to access admin page")


# -----------Create Show--------------------
@app.route('/add_show',methods=["GET","POST"])
def add_show():
    if ('email' in session):
        if request.method == "GET":
            heading = "Add Show"
            form_conditions=[{"type":"text" ,"name":"show_name", "placeholder":"show" ,"required":"True"},
                             {"type":"text", "name":"show_tag", "placeholder":"tag(required)", "required":"True"},
                             {"type":"text", "name":"show_lang","placeholder":"language of show","required":"True"},
                             {"type":"text","name":"show_duration","placeholder":"duration(hh:mm:ss)","required":"True"},
                             {"type":"text" ,"name":"show_discription", "placeholder":"About Show", "required":"False"},
                             {"type":"file" ,"name":"file" ,"placeholder":"upload poster",  "required":"True"}]
            return (render_template("admin.html", take_input="True",special_form="False", display_table = "False", heading=heading, form_conditions=form_conditions))
        if request.method == "POST":
            show_name = request.form['show_name']
            show_tag = request.form['show_tag']
            show_discription = request.form['show_discription']
            show_lang = request.form['show_lang']
            show_duration = request.form['show_duration']
            f=request.files['file']
            f.save('static/image/poster/'+f.filename)
            show_image_path = str('./static/image/poster/'+f.filename)
            record = Show(show_name,show_tag,show_discription,show_lang,show_duration,show_image_path)
            db.session.add(record)
            db.session.commit()
            return redirect('/show_admin')
    else:
        return ("You are not allowed to access admin page")


# ---------------Update Show-------------
@app.route('/edit_show/<int:id>',methods=["POST","GET"])
def edit_show(id):
    if ('email' in session):
        if request.method == "GET":
            content=Show.query.filter_by(show_id=id).first()
            return render_template('edit_show.html', content=content)
        if request.method=="POST":
            content=Show.query.filter_by(show_id=id).first()
            content.show_name = request.form['show_name']
            content.show_tag = request.form['show_tag']
            content.show_discription = request.form['show_discription']
            content.show_duration = request.form['show_duration']
            f=request.files['file']
            if f:
                f.save('./static/image/poster/'+f.filename)
                content.show_image_path = './static/image/poster/'+f.filename
            db.session.commit()
            return redirect('/show_admin')
    else:
        return ("You are not allowed to access admin page")


# ------------Delete Shows-----------
@app.route("/delete_show/<int:id>")
def delete_show(id):
    if ('email' in session):
        # delete all the ticket of show 
        show_venues= Show_venue.query.filter_by(show_id = id).all()
        for show_venue in show_venues:
            # delete dynamic of show venue
            dynamic = Dynamic.query.filter_by(update_id = show_venue.show_venue_id).first()
            if dynamic:
                db.session.delete(dynamic)
                db.session.commit()
            content_linked = delete(Ticket_booked).where(Ticket_booked.show_venue_id == show_venue.show_venue_id)
            db.session.execute(content_linked)
            db.session.commit()
        # delete show rating
        content = Show_rating.query.filter_by(show_id = id).first()
        db.session.delete(content)
        db.session.commit()
        # delete all show venue related to show
        content_linked = delete(Show_venue).where(Show_venue.show_id == id)
        db.session.execute(content_linked)
        db.session.commit()
        # delete show
        content=Show.query.filter_by(show_id=id).first()
        db.session.delete(content)
        db.session.commit()
        return redirect('/show_admin')
    else:
        return ("You are not allowed to access admin page")


# display  which venue alloacted to which show and price of ticket and show time
@app.route('/show_venue_admin', methods=["GET","POST"])
def show_venue():
    if ('email' in session):
        show_venues = Show_venue.query.join(Show,  Venue).filter(Show_venue.show_id == Show.show_id).filter(Show_venue.venue_id == Venue.venue_id).add_columns(Show_venue.show_venue_id,Venue.venue_name, Show.show_name, Show_venue.show_price, Show_venue.show_timing ,Show_venue.show_added_timing).all()
        heading = "Shows with Booking Online"
        show_venue_of_running_shows=[]
        show_venue_of_past_shows = []
        for  show_venue in show_venues:
            show_start_time = datetime.strptime(str(show_venue["show_timing"]), '%Y-%m-%d %H:%M:%S')  # Convert the show start time string to a datetime object
            if (show_start_time < datetime.now()):
                show_venue_of_past_shows.append(show_venue)
            else:
                show_venue_of_running_shows.append(show_venue)
        main_contents = show_venue_of_running_shows
        past_show = True
        main_contents_past_shows = show_venue_of_past_shows
        heads = ["Show Venue Id", "Show Name", "Venue Name", "Price Of Ticket", "Show Timing", "Show Added Timing"]
        box_contents = ["show_venue_id" , "show_name" , "venue_name" , "show_price", "show_timing", "show_added_timing"]
        button = "Book Show Venue"
        button_url = "book_show_venue"
        return render_template('admin.html' ,display_table = "True", take_input = "False", edit_delete = "False" ,input_button="True", heading=heading, main_contents = main_contents,past_show = past_show ,main_contents_past_shows=main_contents_past_shows, heads = heads, box_contents = box_contents, button_name = button, button_url = button_url)
    else:
        return ("You are not allowed to access admin page")


# allocate shows to venue with different pricing and staring time of show
@app.route("/book_show_venue",methods=["GET","POST"])
def book_show_venue():
    if ('email' in session):
        if request.method == "GET":
            venue=Venue.query.all()
            show=Show.query.all()
            heading = "Book Show Venue"
            return render_template("admin.html", take_input="True",special_form="True", display_table = "False", heading=heading, venues = venue, shows=show)
        if request.method == "POST":
            venue=request.form['venue_name']
            show=request.form['show_name']
            price=request.form['price']
            show_time=request.form['showtime']
            show_time = datetime.strptime(show_time,"%Y-%m-%dT%H:%M")
            show_added_timing = datetime.now()
            venue_full = Venue.query.filter_by(venue_name=venue).first()
            show_full = Show.query.filter_by(show_name=show).first()
            record = Show_venue(show = show_full,venue = venue_full, show_price = price ,show_timing = show_time, show_added_timing= show_added_timing)
            db.session.add(record)
            db.session.commit()
            return redirect('/show_venue_admin')
    else:
        return ("You are not allowed to access admin page")
    
