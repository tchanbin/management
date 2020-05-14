from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown

from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
# from app.exceptions import ValidationError
from management import db, login_manager


class Permission:
    APPLY = 1
    CONFIRM = 2
    L1_APPROVAL = 4
    L2_APPROVAL = 8


# 用户角色表
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0


# 用户表
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    department = db.Column(db.String(64))
    company = db.Column(db.String(64))
    tel = db.Column(db.String(15))
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    status = db.Column(db.String(10))

    # car_procedure_infos = db.relationship('CarProcedureInfo', foreign_keys=[])
    # car_procedure_infos_first = db.relationship('CarProcedureInfo', backref='first_users', lazy='dynamic')
    # car_procedure_infos_second = db.relationship('CarProcedureInfo', backref='second_users', lazy='dynamic')
    # car_procedure_infos_confirm = db.relationship('CarProcedureInfo', backref='confirm_users', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # if self.role is None:
        #     if self.email == current_app.config['FLASKY_ADMIN']:
        #         self.role = Role.query.filter_by(name='Administrator').first()
        #     if self.role is None:
        #         self.role = Role.query.filter_by(default=True).first()
        # if self.email is not None and self.avatar_hash is None:
        #     self.avatar_hash = self.gravatar_hash()
        # self.follow(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def jsonstr(self):
        jsonstr = {
            "user_id": self.id,
            "altername": self.username,
            "alterdepartment": self.department,
            "altertel": self.tel,
            "alterrolename": self.role.name,
            "alterroleid": self.role_id,

        }
        return jsonstr


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 公司部门表
class CompanyDepartment(db.Model):
    __tablename__ = 'company_departments'
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(20))
    department = db.Column(db.String(20))


# 流程清单表
class ProcedureList(db.Model):
    __tablename__ = 'procedure_lists'
    id = db.Column(db.Integer, primary_key=True)
    no = db.Column(db.Integer)
    name = db.Column(db.String(10), unique=True)
    description = db.Column(db.String(10))
    procedure_lists = db.relationship("CarProcedureInfo", backref="procedure_name", lazy='dynamic')


# 车辆清单
class CarList(db.Model):
    __tablename__ = 'car_lists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), unique=True)
    car_status = db.Column(db.String(10))
    company = db.Column(db.String(10))
    car_procedure_infos = db.relationship('CarProcedureInfo', backref='cars', lazy='dynamic')


# 流程节点表
class ProcedureNode(db.Model):
    __tablename__ = 'procedure_nodes'
    id = db.Column(db.Integer, primary_key=True)
    no = db.Column(db.Integer)
    name = db.Column(db.String(25))
    parent_id = db.Column(db.Integer)
    role = db.Column(db.String(25))
    description = db.Column(db.String(25))


# 流程线表
class ProcedureLine(db.Model):
    __tablename__ = 'procedure_lines'
    id = db.Column(db.Integer, primary_key=True)
    no = db.Column(db.Integer)
    pre_line_id = db.Column(db.Integer)
    pre_line_name = db.Column(db.String(25))
    next_line_id = db.Column(db.Integer)
    next_line_name = db.Column(db.String(25))
    description = db.Column(db.String(25))


# 流程审批表
class ProcedureApproval(db.Model):
    __tablename__ = 'procedure_approval'
    id = db.Column(db.Integer, primary_key=True)
    procedure_id = db.Column(db.Integer)
    current_line_node_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    user_name = db.Column(db.String(25))
    reason = db.Column(db.String(25))
    approval_time = db.Column(db.DateTime(), default=datetime.now)


# 用车流程信息表
class CarProcedureInfo(db.Model):
    __tablename__ = 'car_procedure_infos'
    id = db.Column(db.Integer, primary_key=True)
    procedure_list_id = db.Column(db.Integer, db.ForeignKey('procedure_lists.id'))
    procedure_no = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tel = db.Column(db.String(15))
    users = db.relationship('User', foreign_keys=user_id, backref="car_procedure_infos",
                            single_parent=True)
    department = db.Column(db.String(64))
    car_id = db.Column(db.Integer, db.ForeignKey('car_lists.id'))
    approval_time = db.Column(db.DateTime(), default=datetime.now)
    book_start_datetime = db.Column(db.DATETIME())
    book_end_datetime = db.Column(db.DATETIME())
    actual_start_datetime = db.Column(db.DATETIME())
    actual_end_datetime = db.Column(db.DATETIME())
    number = db.Column(db.String(20))
    namelist = db.Column(db.String(50))
    reason = db.Column(db.String(128))
    etc = db.Column(db.Boolean, default=False)
    arrival_place = db.Column(db.String(30))
    first_approval = db.Column(db.Integer, db.ForeignKey('users.id'))
    # first_users = db.relationship('User', foreign_keys=[first_approval], backref="car_procedure_infos_first",
    #                               single_parent=True)
    # status1 = db.Column(db.Integer)
    # second_approval = db.Column(db.Integer, db.ForeignKey('users.id'))
    # second_users = db.relationship('User', foreign_keys=[second_approval], backref="car_procedure_infos_second",
    #                                single_parent=True)
    # status2 = db.Column(db.Integer)
    confirmer = db.Column(db.Integer, db.ForeignKey('users.id'))
    car_procedure_infos_confirm = db.relationship('User', foreign_keys=[confirmer],
                                                  backref="car_procedure_infos_confirm", single_parent=True)
    miles = db.Column(db.Integer)
    outmiles = db.Column(db.Integer)
    company = db.Column(db.String(10))
    driver = db.Column(db.String(10))
    rejectreason = db.Column(db.String(100))
    procedure_no = db.Column(db.Integer)
    current_line_node_id = db.Column(db.Integer)
    state = db.Column(db.String(10))

    def jsonstr(self):
        jsonstr = {
            "id": self.id,
            "user_name": self.users.username if self.user_id else "",
            "tel": self.tel,
            "department": self.department,
            "car_name": self.cars.name if self.car_id else "",
            "approval_time": self.approval_time.strftime("%Y-%m-%d %H:%M:%S") if self.approval_time else "",
            "book_start_datetime": self.book_start_datetime.strftime(
                "%Y-%m-%d %H:%M:%S") if self.book_start_datetime else "",
            "book_end_datetime": self.book_end_datetime.strftime("%Y-%m-%d %H:%M:%S") if self.book_end_datetime else "",
            "actual_start_datetime": self.actual_start_datetime.strftime(
                "%Y-%m-%d %H:%M:%S") if self.actual_start_datetime else "",
            "actual_end_datetime": self.actual_end_datetime.strftime(
                "%Y-%m-%d %H:%M:%S") if self.actual_end_datetime else "",
            "number": self.number,
            "namelist": self.namelist,
            "reason": self.reason,
            "etc": "使用ETC" if self.etc else "未使用ETC",
            "arrival_place": self.arrival_place,
            "first_approval": self.first_users.username if self.first_approval else "",
            "status1": "一级审批中" if self.status1 == 0 else "审批通过" if self.status1 == 1 else "一级审批被拒绝",
            "second_approval": self.second_users.username if self.second_approval else "",
            "status2": "二级审批中" if self.status2 == 0 else "审批通过" if self.status2 == 1 else "二级审批被拒绝",
            "confirmer": self.car_procedure_infos_confirm.username if self.confirmer else "",
            "miles": self.miles,
            "outmiles": self.outmiles,
            "company": self.company,
            "rejectreason": self.rejectreason,
            "driver": self.driver
        }
        return jsonstr


#
# 快递流程信息表
class PackageProcedureInfo(db.Model):
    __tablename__ = 'package_procedure_infos'
    id = db.Column(db.Integer, primary_key=True)
    procedure_list_id = db.Column(db.Integer)
    procedure_name = db.Column(db.String(15))
    logistics_company = db.Column(db.String(50))
    num = db.Column(db.String(50))
    destination_company = db.Column(db.String(100))
    package_name = db.Column(db.String(50))
    payment_method = db.Column(db.String(15))
    approval_person = db.Column(db.String(15))
    approval_department = db.Column(db.String(15))
    collect_person = db.Column(db.String(15))
    collect_department = db.Column(db.String(15))
    status = db.Column(db.String(15))
    approval_time = db.Column(db.DateTime(), default=datetime.now)
    confirm_time = db.Column(db.DateTime())

    def jsonstr(self):
        jsonstr = {
            "id": self.id,
            "logistics_company": self.logistics_company,
            "num": self.num,
            "destination_company": self.destination_company,
            "package_name": self.package_name,
            "payment_method": self.payment_method,
            "approval_person": self.approval_person,
            "approval_department": self.approval_department,
            "collect_person": self.collect_person,
            "collect_department": self.collect_department,
            "approval_time": self.approval_time.strftime("%Y-%m-%d %H:%M:%S"),
            "confirm_time": self.confirm_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return jsonstr


# 会议室表
class House(db.Model):  # 这是房间表
    __tablename__ = 'houses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15))
    company = db.Column(db.String(10))

    def __str__(self):
        return self.name


times = ((1, '8:00-8:30'), (2, '8:30-9:00'), (3, '9:00-9:30'), (4, '9:30-10:00'),
         (5, '10:00-10:30'), (6, '10:30-11:00'), (7, '11:00-11:30'), (8, '11:30-12:00'),
         (9, '12:00-12:30'), (10, '12:30-13:00'), (11, '13:00-13:30'), (12, '13:30-14:00'),
         (13, '14:00-14:30'), (14, '14:30-15:00'), (15, '15:00-15:30'), (16, '15:30-16:00'),
         (17, '16:00-16:30'), (18, '16:30-17:00'), (19, '17:00-17:30'), (20, '17:30-18:00'),
         )


class Order(db.Model):  # 这是会议室预定记录表
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date())
    user = db.Column(db.String(15))
    house = db.Column(db.String(15))
    time = db.Column(db.Integer)
    company = db.Column(db.String(10))

    def __str__(self):
        return self.name
