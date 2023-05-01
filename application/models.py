from .database import db
from flask_login import UserMixin

class Show_venue(db.Model):
    __tablename__ = 'show_venue'
    show_venue_id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.venue_id"))
    show_id = db.Column(db.Integer, db.ForeignKey("show.show_id"))
    show_price = db.Column(db.Float, nullable = False)
    show_timing = db.Column(db.DateTime)
    show_added_timing = db.Column(db.DateTime)

    show = db.relationship('Show', back_populates="venues")
    venue = db.relationship('Venue', back_populates="shows")

    def __init__(self, show_price, show ,venue, show_timing, show_added_timing): #show_timming, show_added_timming):
        self.show_price = show_price
        self.show = show
        self.venue= venue
        self.show_timing = show_timing
        self.show_added_timing = show_added_timing

class Show_rating(db.Model):
    __tablename__='show_rating'
    show_id = db.Column(db.Integer,primary_key = True)
    rating = db.Column(db.Float, nullable=True)
    no_of_rating = db.Column(db.Integer)

    def __init__(self,show_id,rating , no_of_rating):
        self.show_id = show_id
        self.rating =rating
        self.no_of_rating = no_of_rating

class Show(db.Model):
    __tablename__ ='show'
    show_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    show_name = db.Column(db.String(25), nullable= False)
    show_tag = db.Column(db.String(10), nullable=False)
    show_lang = db.Column(db.String(10),nullable = False)
    show_duration = db.Column(db.String(10),nullable=False)
    show_discription = db.Column(db.String(1000))
    show_image_path = db.Column(db.String, nullable= False)

    venues = db.relationship('Show_venue', back_populates='show')


    
    def __init__(self,show_name,show_tag,show_discription,show_lang,show_duration,show_image_path):
        self.show_name= show_name
        self.show_tag = show_tag
        self.show_discription = show_discription
        self.show_lang = show_lang
        self.show_duration = show_duration
        self.show_image_path = show_image_path

class Venue(db.Model):
    __tablename__ = 'venue'
    venue_id = db.Column(db.Integer, autoincrement = True, primary_key=True)
    venue_name = db.Column(db.String, nullable= False)
    capacity = db.Column(db.Integer, nullable=False)
    place = db.Column(db.String(75), nullable = False)
    location = db.Column(db.String(75), nullable = False)
    
    shows = db.relationship('Show_venue' , back_populates="venue")

    
    def __init__(self,venue_name,capacity,place,location):
        self.venue_name= venue_name
        self.capacity = capacity
        self.location = location
        self.place = place





class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(20), unique=True ,nullable = False)
    password = db.Column(db.String(80), nullable = False)

    def __init__(self,email,password):
        self.email=email
        self.password = password
    
    def  get_id(self):
        return (self.id)


class Ticket_booked(db.Model):
    __tablename__ = 'ticket_booked'
    booking_id = db.Column(db.Integer,autoincrement=True,primary_key= True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id") ,nullable = False)
    show_venue_id = db.Column(db.Integer, db.ForeignKey("show_venue.show_venue_id") , nullable= False)
    number_of_ticket_booked = db.Column(db.Integer, nullable = False)
    cost_at_the_time_ticket_booking = db.Column(db.Float, nullable = False)
    time_of_ticket_booked = db.Column(db.DateTime)

    def __init__(self,user_id,show_venue_id,number_of_ticket_booked,cost_at_the_time_of_ticket_booking,time_of_ticket_booked):
        self.user_id = user_id
        self.show_venue_id = show_venue_id
        self.number_of_ticket_booked = number_of_ticket_booked
        self.cost_at_the_time_ticket_booking = cost_at_the_time_of_ticket_booking
        self.time_of_ticket_booked = time_of_ticket_booked


class Dynamic(db.Model):
    __tablename__ = 'dynamic'
    update_id = db.Column(db.Integer, db.ForeignKey("show_venue.show_venue_id"),primary_key = True, nullable = False)
    seat_left = db.Column(db.Integer)
    current_price = db.Column(db.Float)

    def __init__(self,update_id,seat_left,current_price):
        self.update_id=update_id
        self.seat_left = seat_left
        self.current_price = current_price