from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, CarProcedureInfo
from random import randint
from werkzeug.security import generate_password_hash


def fake_users(count=10):
    fake = Faker(locale='zh_CN')
    i = 0
    while i < count:

        u = User(username=fake.user_name(),
                 department=fake.job(),
                 tel=fake.phone_number(),
                 password="123456",
                 role_id=fake.random_int(min=1, max=4, step=1),
                 )
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def fake_car_procedure_infos(count=10):
    fake = Faker(locale='zh_CN')
    i = 0
    while i < count:
        c = CarProcedureInfo(procedure_list_id=fake.random_int(min=1,max=10,step=1),
                             user_id=fake.random_int(min=1, max=15, step=1),
                             department=fake.job(),
                             car_id=fake.random_int(min=1, max=5, step=1),
                             approval_time=fake.date_time_between(start_date='-1d', end_date='now', tzinfo=None),
                             book_start_datetime=fake.date_time_between(start_date='-1d', end_date='now', tzinfo=None),
                             book_end_datetime=fake.date_time_between(start_date='now', end_date='+1d', tzinfo=None),
                             actual_start_datetime=fake.date_time_between(start_date='-1d', end_date='now',
                                                                          tzinfo=None),
                             actual_end_datetime=fake.date_time_between(start_date='now', end_date='+1d', tzinfo=None),
                             number=fake.random_int(min=1, max=5, step=1),
                             namelist=fake.name(),
                             reason=fake.paragraph(nb_sentences=2, variable_nb_sentences=True, ext_word_list=None),
                             etc=fake.boolean(chance_of_getting_true=30),
                             arrival_place=fake.city(),
                             first_approval=fake.random_int(min=1, max=2, step=1),
                             status1=fake.random_int(min=0, max=1, step=1),
                             second_approval=fake.random_int(min=3, max=4, step=1),
                             status2=fake.random_int(min=0, max=1, step=1),
                             confirmer=fake.random_int(min=5, max=6, step=1),
                             miles=fake.random_int(min=10000, max=100000, step=123),

                             )
        db.session.add(c)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()
