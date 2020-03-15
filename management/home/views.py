from flask import render_template, redirect, url_for, abort, flash, request, \
    current_app, make_response, g, session, Response, jsonify, json
from .forms import LoginForm, ResetPwd, CarProcedureForm, MilesForm
from flask_login import login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, extract
from ..models import Permission, Role, User, CarProcedureInfo, CarList, ProcedureList
from . import home
from management import db, excel
from datetime import datetime
from management.decorators import permission_required
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook


# 用户登录
@home.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get("next")
            if next is None or not next.startswith("/"):
                next = url_for("home.index")
            return redirect(next)
        flash("用户名或者密码错误")
    return render_template('home/login.html', form=form)


# 用户主页
@home.route("/index", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def index():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")

    pagination = CarProcedureInfo.query.filter(CarProcedureInfo.user_id == current_user.id,
                                               CarProcedureInfo.approval_time.contains(keywords),

                                               ).order_by(
        CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/index.html", my_procedure=my_procedure, pagination=pagination)


# 发起流程申请页面
@home.route("/startapproval", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def startapproval():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    pagination = ProcedureList.query.filter(
        ProcedureList.name.contains(keywords),
    ).order_by(
        ProcedureList.id.asc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    procedure_lists = pagination.items

    return render_template("home/startapproval.html", procedure_lists=procedure_lists, pagination=pagination)


# 公务用车流程申请表
@home.route("/procedureapproval1", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def procedureapproval1():
    # 生成公务用车流程申请表单对象
    form = CarProcedureForm()

    # 给车名字的下拉列表找到车型
    form.carname.choices = [(c.id, c.name) for c in CarList.query.all()]
    # 查找到所有二级审批通过的车的申请信息
    carusestatus = CarProcedureInfo.query.filter(
        CarProcedureInfo.status2 == 1,
        CarProcedureInfo.actual_end_datetime == None,
    ).order_by(
        CarProcedureInfo.book_start_datetime).all()
    # 对表单的提交内容进行验证
    if form.validate_on_submit():
        car_procedure_approval = CarProcedureInfo(procedure_list_id=1,
                                                  user_id=current_user.id,
                                                  department=current_user.department,
                                                  tel=form.tel.data,
                                                  car_id=form.carname.data,
                                                  book_start_datetime=form.bookstartdatetime.data,
                                                  book_end_datetime=form.bookenddatetime.data,
                                                  number=form.number.data,
                                                  namelist=form.namelist.data,
                                                  arrival_place=form.arrivalplace.data,
                                                  etc=form.ifetc.data,
                                                  status1=0,
                                                  status2=0,

                                                  )

        db.session.add(car_procedure_approval)
        try:
            db.session.commit()
            flash("您的用车申请已经提交成功，请到我的流程查看")
            return redirect(url_for("home.index"))
        except:
            db.session.rollback()
            flash("提交数据失败")
            abort(404)
    return render_template("home/procedureapproval1.html", current_time=datetime.utcnow(), form=form,
                           carusestatus=carusestatus)


# 1级与2级待审批界面
@home.route("/L1L2approval", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def L1L2approval():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    if not current_user.can(Permission.L2_APPROVAL):
        pagination = CarProcedureInfo.query.filter(CarProcedureInfo.department == current_user.department,
                                                   CarProcedureInfo.approval_time.contains(keywords),
                                                   CarProcedureInfo.status1 == 0,

                                                   ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items
    else:
        pagination = CarProcedureInfo.query.filter(and_(
            CarProcedureInfo.approval_time.contains(keywords),
            CarProcedureInfo.status1 != 2,
            CarProcedureInfo.status2 != 2,
            or_(CarProcedureInfo.status1 == 0,
                CarProcedureInfo.status2 == 0, ))
        ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items

    return render_template("home/L1L2approval.html", my_procedure=my_procedure, pagination=pagination)


# 一级审批确认通过流程
@home.route("/L1approvalok/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def L1approvalok(procedure_id):
    # 根据流程id找到该条记录
    procedure = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    # 对该条记录的status1进行更新
    procedure.status1 = 1
    procedure.first_approval = current_user.id

    db.session.add(procedure)
    try:
        db.session.commit()
        flash("您已审批通过一条申请")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 一级审批拒绝流程
@home.route("/L1approvalnok/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def L1approvalnok(procedure_id):
    # 根据流程id找到该条记录
    procedure = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    # 对该条记录的status1进行更新
    procedure.status1 = 2
    procedure.first_approval = current_user.id
    db.session.add(procedure)
    try:
        db.session.commit()
        flash("您已拒绝一条申请")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 二级审批确认通过流程
@home.route("/L2approvalok/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def L2approvalok(procedure_id):
    # 根据流程id找到该条记录
    procedure = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    # 对该条记录的status1进行更新
    procedure.status2 = 1
    procedure.second_approval = current_user.id
    db.session.add(procedure)
    try:
        db.session.commit()
        flash("您已审批通过一条申请")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 二级审批拒绝流程
@home.route("/L2approvalnok/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def L2approvalnok(procedure_id):
    # 根据流程id找到该条记录
    procedure = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    # 对该条记录的status1进行更新
    procedure.status2 = 2
    procedure.second_approval = current_user.id
    db.session.add(procedure)
    try:
        db.session.commit()
        flash("您已拒绝一条申请")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 我的已经审批过的流程清单
@home.route("/myapprovaledprocedure", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def myapprovaledprocedure():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    if not current_user.can(Permission.L2_APPROVAL):
        pagination = CarProcedureInfo.query.filter(CarProcedureInfo.department == current_user.department,
                                                   CarProcedureInfo.approval_time.contains(keywords),
                                                   CarProcedureInfo.first_approval == current_user.id,
                                                   CarProcedureInfo.status1 == 1,

                                                   ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items
    else:
        pagination = CarProcedureInfo.query.filter(and_(
            CarProcedureInfo.approval_time.contains(keywords),
            or_(
                CarProcedureInfo.first_approval == current_user.id,
                CarProcedureInfo.second_approval == current_user.id,
            ),
            or_(
                CarProcedureInfo.status1 == 1,
                CarProcedureInfo.status2 == 1,
            )
        )

        ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items

    return render_template("home/myapprovaledprocedure.html", my_procedure=my_procedure, pagination=pagination, )


# 确认车辆出入流程操作界面
@home.route("/confirmprocedure", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmprocedure():
    page = request.args.get("page", 1, type=int)
    # keywords = request.args.get("keywords", "")
    form = MilesForm()
    if form.validate_on_submit():
        miles = form.miles.data
        procedure_id = form.procedure_id.data
        a = CarProcedureInfo.query.filter(
            CarProcedureInfo.id == procedure_id,
        ).first()
        a.miles = miles
        a.actual_end_datetime = datetime.now()
        db.session.add(a)
        try:
            db.session.commit()
            flash("您已确认车辆进厂，公里数提交成功")
        except:
            db.session.rollback()
            flash("提交数据失败")
            return render_template("404.html")

    pagination = CarProcedureInfo.query.filter(
        # CarProcedureInfo.approval_time.contains(keywords),
        CarProcedureInfo.status2 == 1,
        CarProcedureInfo.actual_end_datetime == None

    ).order_by(
        CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/confirmprocedure.html", my_procedure=my_procedure, pagination=pagination, form=form)


# 确认车辆出厂
@home.route("/confirmleave/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmleave(procedure_id):
    a = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()

    a.actual_start_datetime = datetime.now()
    db.session.add(a)
    try:
        db.session.commit()
        flash("您已确认车辆出厂")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("404.html")

    return redirect(url_for("home.confirmprocedure"))


# 确认车辆入厂
@home.route("/confirmarrive/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmarrive(procedure_id):
    form = MilesForm()
    miles = form.miles.data
    a = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    a.miles = miles

    db.session.add(a)
    try:
        db.session.commit()
        return redirect(url_for("home.success"))
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("404.html")

    return redirect(url_for("home.confirmprocedure"))


# # 提示响应成功地址
# @home.route('/success')
# @login_required
# def success():
#     resp = make_response(redirect(url_for('.confirmleave')))
#     resp.
#     return resp(200)

# @home.before_request
# def homeg():
#     g.ifok = "kong"


# 作废流程页
@home.route("/rejectedprocedure", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def rejectedprocedure():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")

    pagination = CarProcedureInfo.query.filter(
        CarProcedureInfo.approval_time.contains(keywords),
        or_(
            CarProcedureInfo.status1 == 2,
            CarProcedureInfo.status2 == 2,
        ),
        or_(CarProcedureInfo.user_id == current_user.id,
            CarProcedureInfo.first_approval == current_user.id,
            CarProcedureInfo.second_approval == current_user.id
            )

    ).order_by(
        CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/rejectedprocedure.html", my_procedure=my_procedure, pagination=pagination)


# 所有流程清单页
@home.route("/procedurelists", methods=["GET", "POST"])
@login_required
# @permission_required(Permission.L2_APPROVAL)
def procedurelists():
    if request.method == "POST":
        year = request.form.get("year")
        month = request.form.get("month")
        arrays = CarProcedureInfo.query.filter(
            extract("year", CarProcedureInfo.actual_end_datetime) == year,
            extract("month", CarProcedureInfo.actual_end_datetime) == month

        ).order_by(
            CarProcedureInfo.actual_end_datetime.asc()).all()
        if arrays:  # 如果有数据则导出
            column = [["序号","流程编号", "结束日期", "申请人", "目的地","用车原因", "车型", "是否用ETC", "公里数"]]
            i=1
            for  array in arrays:
                list = array.jsonstr()  # 将每一行查询的数据转换成字典格式
                array_content = [i,
                                 list["id"],
                                 list["actual_end_datetime"][0:10],
                                 list["user_name"],
                                 list["arrival_place"],
                                 list["reason"],
                                 list["car_name"],
                                 list["etc"],
                                 ]  # 将每一行的数据需要的先转换成字典，然后把相应内容导出。
                column.append(array_content)
                i+=1
                filename = "用车情况按月统计表" + datetime.now().__str__()[0:10]

            return excel.make_response_from_array(column, file_type="xls", file_name=filename)
        else:
            flash("该月份没有用车记录")
            return redirect(url_for("home.procedurelists"))
    if request.method == "GET":
        page = request.args.get("page", 1, type=int)
        keywords = request.args.get("keywords", "")

        pagination = CarProcedureInfo.query.filter(CarProcedureInfo.user_id == current_user.id,
                                                   CarProcedureInfo.approval_time.contains(keywords),
                                                   ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items
    return render_template("home/procedurelists.html", my_procedure=my_procedure, pagination=pagination)


# 使用openpyxl导出方法，这个可以通过openpyxl对单元格的内容进行操作。
# if request.method == "POST":
#        year = request.form.get("year")
#        month = request.form.get("month")
#        query_sets = CarProcedureInfo.query.filter(
#            extract("year", CarProcedureInfo.actual_end_datetime) == year,
#            extract("month", CarProcedureInfo.actual_end_datetime) == month
#
#        ).order_by(
#            CarProcedureInfo.actual_end_datetime.asc()).all()
#        wb = Workbook()
#        wb.create_sheet("用车信息")
#        ws = wb.active
#        ws["A4"] = 4
#        ws["A1"]="nihao "
#
#        content = save_virtual_workbook(wb)  # 此处这个save_virtual_workbook函数将 Excel 文档写入到内存，返回一个字节数组。
#
#        resp = make_response(content)
#        resp.headers["Content-Disposition"] = 'attachment; filename=carinfos.xlsx'
#        resp.headers['Content-Type'] = 'application/x-xlsx'
#        return resp


# 用户登出
@home.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()

    return redirect(url_for("home.login"))


# 用户修改密码
@home.route("/resetpwd", methods=["GET", "POST"])
@login_required
def resetpwd():
    form = ResetPwd()

    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password2.data
            db.session.add(current_user)
            try:
                db.session.commit()
                flash("您已经成功修改密码")


            except:
                db.session.rollback()
                flash("数据提交失败，请联系管理员")

        else:
            flash("旧密码错误，请重新输入")

    return render_template("home/resetpwd.html", form=form)


# 查询详情页
@home.route("/procedureinfos", methods=["POST"])
@login_required
def procedureinfos():
    data1 = json.loads(request.get_data())
    procedure_id = data1["procedure_id"]
    procedureinfos = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    data = procedureinfos.jsonstr()
    return jsonify(data)
